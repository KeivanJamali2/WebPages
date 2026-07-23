"""
Daily Form models with all sections.
"""
from datetime import datetime
from . import db


class DailyFormSubmission(db.Model):
    """Main daily form submission model."""
    __tablename__ = 'daily_form_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Form identification
    document_code = db.Column(db.String(100), unique=True, nullable=False)
    
    # Date and Time info
    form_date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.String(20))
    work_shift = db.Column(db.String(50))
    
    # Foreign Keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Status: draft, pending, approved, rejected
    status = db.Column(db.String(20), default='draft')
    
    # Review info
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_comment = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Document attachments - stores path to the zip file containing all documents
    documents_path = db.Column(db.String(500), nullable=True)
    
    # Relationships to form sections
    human_resources = db.relationship('HumanResource', backref='daily_form', lazy='dynamic',
                                       cascade='all, delete-orphan')
    tools_equipments = db.relationship('ToolEquipment', backref='daily_form', lazy='dynamic',
                                        cascade='all, delete-orphan')
    construction_operations = db.relationship('ConstructionOperation', backref='daily_form', lazy='dynamic',
                                               cascade='all, delete-orphan')
    incoming_materials = db.relationship('IncomingMaterial', backref='daily_form', lazy='dynamic',
                                          cascade='all, delete-orphan')
    climate_conditions = db.relationship('ClimateCondition', backref='daily_form', lazy='dynamic',
                                          cascade='all, delete-orphan')
    project_issues = db.relationship('ProjectIssue', backref='daily_form', lazy='dynamic',
                                      cascade='all, delete-orphan')
    safety_records = db.relationship('Safety', backref='daily_form', lazy='dynamic',
                                      cascade='all, delete-orphan')
    events = db.relationship('Event', backref='daily_form', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    # Reviewer relationship
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_forms')
    
    # Comments
    comments = db.relationship('Comment', backref='daily_form', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DailyForm {self.document_code} - {self.form_date}>'
    
    def submit(self):
        """Submit the form for review."""
        self.status = 'pending'
        self.submitted_at = datetime.utcnow()
    
    def approve(self, reviewer_id, comment=None):
        """Approve the form."""
        self.status = 'approved'
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_comment = comment
    
    def reject(self, reviewer_id, comment):
        """Reject the form - sends back to draft for revision."""
        self.status = 'draft'  # Back to draft so employee can edit
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.review_comment = comment
    
    def to_dict(self, include_sections=False):
        data = {
            'id': self.id,
            'document_code': self.document_code,
            'form_date': self.form_date.isoformat() if self.form_date else None,
            'day_of_week': self.day_of_week,
            'work_shift': self.work_shift,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'submitted_by': self.submitted_by,
            'submitted_by_username': self.submitted_by_user.username if self.submitted_by_user else None,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }
        
        if include_sections:
            data['human_resources'] = [hr.to_dict() for hr in self.human_resources]
            data['tools_equipments'] = [te.to_dict() for te in self.tools_equipments]
            data['construction_operations'] = [co.to_dict() for co in self.construction_operations]
            data['incoming_materials'] = [im.to_dict() for im in self.incoming_materials]
            data['climate_conditions'] = [cc.to_dict() for cc in self.climate_conditions]
            data['project_issues'] = [pi.to_dict() for pi in self.project_issues]
            data['safety_records'] = [sr.to_dict() for sr in self.safety_records]
            data['events'] = [e.to_dict() for e in self.events]
        
        return data


class HumanResource(db.Model):
    """Human Resources section of daily form."""
    __tablename__ = 'human_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    post = db.Column(db.String(100), nullable=False)  # Position/Role
    count = db.Column(db.Integer, default=0)  # Number of people
    working_hours = db.Column(db.Float, default=0)  # Hours of working
    notes = db.Column(db.Text)  # Explanations
    
    def to_dict(self):
        return {
            'id': self.id,
            'post': self.post,
            'count': self.count,
            'working_hours': self.working_hours,
            'notes': self.notes
        }


class ToolEquipment(db.Model):
    """Tools and Equipment section of daily form."""
    __tablename__ = 'tools_equipments'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    equipment_type = db.Column(db.String(100), nullable=False)  # Type/Category (required)
    equipment_model = db.Column(db.String(100), nullable=True)  # Model/Variant (optional)
    count_active = db.Column(db.Integer, default=0)
    working_hours = db.Column(db.Float, default=0)
    situation = db.Column(db.String(50))  # Active, Inactive, Under Repair
    inactivity_reason = db.Column(db.Text)
    
    # For backward compatibility
    @property
    def equipment_name(self):
        """Return combined name for backward compatibility."""
        if self.equipment_model:
            return f"{self.equipment_type} - {self.equipment_model}"
        return self.equipment_type
    
    def to_dict(self):
        return {
            'id': self.id,
            'equipment_type': self.equipment_type,
            'equipment_model': self.equipment_model,
            'equipment_name': self.equipment_name,  # For backward compatibility
            'count_active': self.count_active,
            'working_hours': self.working_hours,
            'situation': self.situation,
            'inactivity_reason': self.inactivity_reason
        }


class ConstructionOperation(db.Model):
    """Construction Operations section of daily form."""
    __tablename__ = 'construction_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    operation_type = db.Column(db.String(255), nullable=False)
    start_station = db.Column(db.String(20))  # Station format like "00+000", "100+150"
    end_station = db.Column(db.String(20))    # Station format like "00+200", "100+350"
    unit = db.Column(db.String(50))  # meters, cubic meters, etc.
    amount = db.Column(db.Float, default=0)  # Amount of work done in the unit
    
    @staticmethod
    def station_to_meters(station):
        """Convert station format (00+000) to meters."""
        if not station:
            return 0
        try:
            # Handle format like "00+000" or "100+150"
            if '+' in str(station):
                parts = str(station).split('+')
                km = int(parts[0])
                meters = int(parts[1]) if len(parts) > 1 else 0
                return km * 1000 + meters
            else:
                return float(station)
        except:
            return 0
    
    @staticmethod
    def meters_to_station(meters):
        """Convert meters to station format (00+000)."""
        if meters is None:
            return ""
        try:
            meters = float(meters)
            km = int(meters // 1000)
            m = int(meters % 1000)
            return f"{km:02d}+{m:03d}"
        except:
            return ""
    
    @property
    def start_meters(self):
        """Get start position in meters."""
        return self.station_to_meters(self.start_station)
    
    @property
    def end_meters(self):
        """Get end position in meters."""
        return self.station_to_meters(self.end_station)
    
    @property
    def length_meters(self):
        """Get length of operation in meters."""
        return self.end_meters - self.start_meters
    
    def to_dict(self):
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'start_station': self.start_station,
            'end_station': self.end_station,
            'start_meters': self.start_meters,
            'end_meters': self.end_meters,
            'length_meters': self.length_meters,
            'unit': self.unit,
            'amount': self.amount
        }


class IncomingMaterial(db.Model):
    """Incoming Materials and Goods section of daily form."""
    __tablename__ = 'incoming_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    material_type = db.Column(db.String(255), nullable=False)
    material_unit = db.Column(db.String(50))  # Unit of measurement (auto-filled from config)
    incoming_amount = db.Column(db.Float, default=0)
    cumulative_incoming = db.Column(db.Float, default=0)
    used_amount = db.Column(db.Float, default=0)
    cumulative_used = db.Column(db.Float, default=0)
    storage_place = db.Column(db.String(255))
    waybill_number = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_type': self.material_type,
            'material_unit': self.material_unit,
            'incoming_amount': self.incoming_amount,
            'cumulative_incoming': self.cumulative_incoming,
            'used_amount': self.used_amount,
            'cumulative_used': self.cumulative_used,
            'storage_place': self.storage_place,
            'waybill_number': self.waybill_number
        }


class ClimateCondition(db.Model):
    """Climate Condition section of daily form."""
    __tablename__ = 'climate_conditions'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    min_temperature = db.Column(db.Float)
    max_temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    
    # Weather type - single selection (clear, cloudy, rainy, foggy, snowy)
    weather_type = db.Column(db.String(50))
    
    # Wind speed - single selection (fast, normal, slow)
    wind_speed = db.Column(db.String(50))
    
    # Climate effect on project - single selection (no_effect, slow_progress, stopped)
    climate_effect = db.Column(db.String(50))
    
    # Legacy fields - kept for backward compatibility
    is_clear = db.Column(db.Boolean, default=False)
    is_cloudy = db.Column(db.Boolean, default=False)
    is_rainy = db.Column(db.Boolean, default=False)
    is_foggy = db.Column(db.Boolean, default=False)
    is_snowy = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'min_temperature': self.min_temperature,
            'max_temperature': self.max_temperature,
            'humidity': self.humidity,
            'weather_type': self.weather_type,
            'wind_speed': self.wind_speed,
            'climate_effect': self.climate_effect,
            'is_clear': self.is_clear,
            'is_cloudy': self.is_cloudy,
            'is_rainy': self.is_rainy,
            'is_foggy': self.is_foggy,
            'is_snowy': self.is_snowy
        }


class ProjectIssue(db.Model):
    """Project Issues section of daily form."""
    __tablename__ = 'project_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    issue_type = db.Column(db.String(255), nullable=False)
    effect = db.Column(db.Text)
    location_station = db.Column(db.String(20))  # Station format: 00+000
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_type': self.issue_type,
            'effect': self.effect,
            'location_station': self.location_station,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'notes': self.notes
        }


class Safety(db.Model):
    """Safety section of daily form."""
    __tablename__ = 'safety_records'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    safety_situation = db.Column(db.String(100))  # Incident, NearMiss, NoIncident
    safety_inspection = db.Column(db.Boolean, default=False)
    incident_occurred = db.Column(db.Boolean, default=False)
    incident_explanation = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'safety_situation': self.safety_situation,
            'safety_inspection': self.safety_inspection,
            'incident_occurred': self.incident_occurred,
            'incident_explanation': self.incident_explanation
        }


class Event(db.Model):
    """Events section of daily form."""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    daily_form_id = db.Column(db.Integer, db.ForeignKey('daily_form_submissions.id'), nullable=False)
    
    event_type = db.Column(db.String(50))  # Visit, Meeting, Other
    event_name = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text)
    document_filename = db.Column(db.String(255))  # Filename of uploaded document (stored in ZIP/events/)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_name': self.event_name,
            'explanation': self.explanation,
            'document_filename': self.document_filename
        }
