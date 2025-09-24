from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime, date
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hologram_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Carton(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carton_no = db.Column(db.String(50), unique=True, nullable=False)
    start_series = db.Column(db.Integer, nullable=False)
    end_series = db.Column(db.Integer, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    boxes = db.relationship('Box', backref='carton', lazy=True, cascade='all, delete-orphan')

class Box(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    carton_id = db.Column(db.Integer, db.ForeignKey('carton.id'), nullable=False)
    box_no = db.Column(db.Integer, nullable=False)
    start_series = db.Column(db.Integer, nullable=False)
    end_series = db.Column(db.Integer, nullable=False)
    issued_upto = db.Column(db.Integer, default=0)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_no = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.Date, default=date.today)
    total_required = db.Column(db.Integer, nullable=False)
    series_from = db.Column(db.Integer, nullable=False)
    series_to = db.Column(db.Integer, nullable=False)
    permits = db.relationship('Permit', backref='issue', lazy=True, cascade='all, delete-orphan')

class Permit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), nullable=False)
    permit_no = db.Column(db.String(50), nullable=False)
    permit_date = db.Column(db.Date, nullable=False)

# Forms
class CartonForm(FlaskForm):
    carton_no = StringField('Carton Number', validators=[DataRequired()])
    start_series = IntegerField('Starting Series Number', validators=[DataRequired(), NumberRange(min=1)])
    end_series = IntegerField('Ending Series Number', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Carton')

class IssueForm(FlaskForm):
    issue_no = StringField('Issue Number', validators=[DataRequired()])
    total_required = IntegerField('Total Holograms Required', validators=[DataRequired(), NumberRange(min=1)])
    permits = TextAreaField('Permit Numbers (one per line with format: PERMIT_NO|YYYY-MM-DD)', validators=[DataRequired()])
    submit = SubmitField('Issue Holograms')

# Helper Functions
def get_next_available_series(quantity):
    """Get the next available series for issuance"""
    boxes = Box.query.order_by(Box.carton_id, Box.box_no).all()
    
    start_series = None
    end_series = None
    remaining_quantity = quantity
    
    for box in boxes:
        available_in_box = (box.end_series - box.start_series + 1) - box.issued_upto
        
        if available_in_box > 0:
            if start_series is None:
                start_series = box.start_series + box.issued_upto
            
            if remaining_quantity <= available_in_box:
                end_series = box.start_series + box.issued_upto + remaining_quantity - 1
                # Update the box's issued_upto
                box.issued_upto += remaining_quantity
                break
            else:
                remaining_quantity -= available_in_box
                box.issued_upto = box.end_series - box.start_series + 1
                end_series = box.end_series
    
    db.session.commit()
    
    if start_series is None or end_series is None or remaining_quantity > 0:
        return None, None  # Not enough stock
    
    return start_series, end_series

def get_total_stock():
    """Get total available stock"""
    total_stock = 0
    boxes = Box.query.all()
    for box in boxes:
        available_in_box = (box.end_series - box.start_series + 1) - box.issued_upto
        total_stock += available_in_box
    return total_stock

# Routes
@app.route('/')
def dashboard():
    total_cartons = Carton.query.count()
    total_issues = Issue.query.count()
    total_stock = get_total_stock()
    recent_issues = Issue.query.order_by(Issue.issue_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_cartons=total_cartons,
                         total_issues=total_issues,
                         total_stock=total_stock,
                         recent_issues=recent_issues)

@app.route('/add_carton', methods=['GET', 'POST'])
def add_carton():
    form = CartonForm()
    if form.validate_on_submit():
        # Check if carton number already exists
        existing_carton = Carton.query.filter_by(carton_no=form.carton_no.data).first()
        if existing_carton:
            flash('Carton number already exists!', 'error')
            return render_template('add_carton.html', form=form)
        
        # Validate series range
        if form.end_series.data is None or form.start_series.data is None or form.end_series.data <= form.start_series.data:
            flash('End series must be greater than start series!', 'error')
            return render_template('add_carton.html', form=form)
        
        # Check if series range is exactly 100,000
        total_holograms = form.end_series.data - form.start_series.data + 1
        if total_holograms != 100000:
            flash('Each carton must contain exactly 100,000 holograms!', 'error')
            return render_template('add_carton.html', form=form)
        
        # Create carton
        carton = Carton()
        carton.carton_no = form.carton_no.data
        carton.start_series = form.start_series.data
        carton.end_series = form.end_series.data
        db.session.add(carton)
        db.session.flush()  # Get the carton ID
        
        # Create 5 boxes automatically
        box_size = 20000
        for i in range(5):
            box_start = form.start_series.data + (i * box_size)
            box_end = box_start + box_size - 1
            
            box = Box()
            box.carton_id = carton.id
            box.box_no = i + 1
            box.start_series = box_start
            box.end_series = box_end
            box.issued_upto = 0
            db.session.add(box)
        
        db.session.commit()
        flash('Carton added successfully with 5 boxes created!', 'success')
        return redirect(url_for('view_stock'))
    
    return render_template('add_carton.html', form=form)

@app.route('/view_stock')
def view_stock():
    cartons = Carton.query.order_by(Carton.created_date.desc()).all()
    carton_data = []
    
    for carton in cartons:
        boxes_info = []
        for box in carton.boxes:
            available = (box.end_series - box.start_series + 1) - box.issued_upto
            boxes_info.append({
                'box_no': box.box_no,
                'start_series': box.start_series,
                'end_series': box.end_series,
                'issued_upto': box.issued_upto,
                'available': available
            })
        
        carton_data.append({
            'carton': carton,
            'boxes': boxes_info,
            'total_available': sum(box['available'] for box in boxes_info)
        })
    
    return render_template('view_stock.html', carton_data=carton_data)

@app.route('/issue_holograms', methods=['GET', 'POST'])
def issue_holograms():
    form = IssueForm()
    total_stock = get_total_stock()
    
    if form.validate_on_submit():
        # Check if issue number already exists
        existing_issue = Issue.query.filter_by(issue_no=form.issue_no.data).first()
        if existing_issue:
            flash('Issue number already exists!', 'error')
            return render_template('issue_holograms.html', form=form, total_stock=total_stock)
        
        # Check stock availability
        if form.total_required.data is None or form.total_required.data > total_stock:
            flash(f'Insufficient stock! Available: {total_stock}', 'error')
            return render_template('issue_holograms.html', form=form, total_stock=total_stock)
        
        # Get next available series
        series_from, series_to = get_next_available_series(form.total_required.data)
        if series_from is None:
            flash('Error allocating series numbers!', 'error')
            return render_template('issue_holograms.html', form=form, total_stock=total_stock)
        
        # Create issue
        issue = Issue()
        issue.issue_no = form.issue_no.data
        issue.total_required = form.total_required.data
        issue.series_from = series_from
        issue.series_to = series_to
        db.session.add(issue)
        db.session.flush()
        
        # Parse and add permits
        permits_text = form.permits.data or ""
        permits_text = permits_text.strip()
        for line in permits_text.split('\n'):
            if '|' in line:
                parts = line.strip().split('|')
                if len(parts) == 2:
                    permit_no = parts[0].strip()
                    try:
                        permit_date = datetime.strptime(parts[1].strip(), '%Y-%m-%d').date()
                        permit = Permit()
                        permit.issue_id = issue.id
                        permit.permit_no = permit_no
                        permit.permit_date = permit_date
                        db.session.add(permit)
                    except ValueError:
                        flash(f'Invalid date format for permit {permit_no}. Use YYYY-MM-DD', 'error')
                        return render_template('issue_holograms.html', form=form, total_stock=total_stock)
        
        db.session.commit()
        flash(f'Holograms issued successfully! Series: {series_from} to {series_to}', 'success')
        return redirect(url_for('view_issues'))
    
    return render_template('issue_holograms.html', form=form, total_stock=total_stock)

@app.route('/view_issues')
def view_issues():
    issues = Issue.query.order_by(Issue.issue_date.desc()).all()
    return render_template('view_issues.html', issues=issues)

@app.route('/monthly_report')
def monthly_report():
    # Get month and year from query params
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get issues for the specified month
    issues = Issue.query.filter(
        db.extract('month', Issue.issue_date) == month,
        db.extract('year', Issue.issue_date) == year
    ).order_by(Issue.issue_date).all()
    
    total_issued = sum(issue.total_required for issue in issues)
    remaining_stock = get_total_stock()
    
    return render_template('monthly_report.html', 
                         issues=issues, 
                         month=month, 
                         year=year,
                         total_issued=total_issued,
                         remaining_stock=remaining_stock)

@app.route('/export_pdf')
def export_pdf():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # Get issues for the specified month
    issues = Issue.query.filter(
        db.extract('month', Issue.issue_date) == month,
        db.extract('year', Issue.issue_date) == year
    ).order_by(Issue.issue_date).all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph(f'Hologram Issuance Report - {month:02d}/{year}', title_style))
    story.append(Spacer(1, 20))
    
    # Table data
    data = [['Date', 'Issue No', 'Permit Nos', 'Series From', 'Series To', 'Total Issued']]
    
    for issue in issues:
        permit_nos = ', '.join([permit.permit_no for permit in issue.permits])
        data.append([
            issue.issue_date.strftime('%Y-%m-%d'),
            issue.issue_no,
            permit_nos,
            str(issue.series_from),
            str(issue.series_to),
            str(issue.total_required)
        ])
    
    # Add totals
    total_issued = sum(issue.total_required for issue in issues)
    remaining_stock = get_total_stock()
    
    data.append(['', '', '', '', 'Total Issued:', str(total_issued)])
    data.append(['', '', '', '', 'Remaining Stock:', str(remaining_stock)])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -3), colors.beige),
        ('BACKGROUND', (0, -2), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'hologram_report_{month:02d}_{year}.pdf',
        mimetype='application/pdf'
    )

# API endpoint for calculator
@app.route('/api/calculate_holograms', methods=['POST'])
def calculate_holograms():
    data = request.get_json()
    bottles = data.get('bottles', 0)
    cases = data.get('cases', 0)
    
    try:
        bottles = int(bottles) if bottles else 0
        cases = int(cases) if cases else 0
        holograms = bottles * cases
        return jsonify({'holograms': holograms})
    except (ValueError, TypeError):
        return jsonify({'holograms': 0})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)