from app import celery, app
from models import db, User, Drive, Application
import csv
import os
from datetime import datetime


# ASYNC JOB: Export CSV

@celery.task(name="export_student_applications_csv")
def export_student_applications_csv(student_id, student_email):

    # Fetch the student's applications
    applications = Application.query.filter_by(student_id=student_id).all()
    
    # Define file path
    filename = f"export_{student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    filepath = os.path.join(app.config.get('EXPORT_FOLDER', 'static/exports'), filename)
    
    # Generate CSV
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Application ID', 'Company Name', 'Job Title', 'Status', 'Date Applied'])
        
        for app_record in applications:
            writer.writerow([
                app_record.id,
                app_record.drive.company.username,
                app_record.drive.job_title,
                app_record.status,
                app_record.applied_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
            
  
    print(f"[CELERY ALERT] CSV Export complete for Student ID {student_id}. File saved at {filepath}")
    
    return filepath


# SCHEDULED JOB 1: Daily Reminders

@celery.task(name="send_daily_reminders")
def send_daily_reminders():
   
    pending_drives = Drive.query.filter_by(status='Pending').count()
    print(f"[CELERY DAILY JOB] Admin Alert: There are {pending_drives} placement drives awaiting approval.")
    return "Daily reminders sent."


# SCHEDULED JOB 2: Monthly HTML Report

@celery.task(name="generate_monthly_report")
def generate_monthly_report():
    """
    Runs on the 1st of every month. Generates a placement activity report.
    """
    total_drives = Drive.query.count()
    total_selected = Application.query.filter_by(status='Selected').count()
    
    # Simulated HTML email generation
    html_report = f"""
    <h1>Monthly Placement Report</h1>
    <p>Total Drives Conducted: {total_drives}</p>
    <p>Total Students Selected: {total_selected}</p>
    """
    
    print("[CELERY MONTHLY JOB] Monthly HTML report generated and emailed to Admin.")
    print(html_report)
    return "Monthly report generated."