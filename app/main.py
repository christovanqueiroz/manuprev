from __future__ import annotations

from datetime import datetime
from io import BytesIO

from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func

from .indicators import calculate_indicators


db = SQLAlchemy()


class Equipment(db.Model):
    __tablename__ = "equipments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    serial_number = db.Column(db.String(120), unique=True, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PreventivePlan(db.Model):
    __tablename__ = "preventive_plans"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipments.id"), nullable=False)
    frequency_days = db.Column(db.Integer, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    activities = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)


class CorrectiveRecord(db.Model):
    __tablename__ = "corrective_records"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipments.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    failure_start = db.Column(db.DateTime, nullable=False)
    repair_end = db.Column(db.DateTime, nullable=False)
    root_cause = db.Column(db.Text, nullable=False)
    actions_taken = db.Column(db.Text, nullable=False)



def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)



def create_pdf_report(equipments: list[Equipment], indicators: dict[int, dict[str, float | None]]) -> BytesIO:
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4)
    width, height = A4

    y = height - 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Relatório de Manutenção Preventiva")
    y -= 30

    pdf.setFont("Helvetica", 10)
    for equipment in equipments:
        data = indicators.get(equipment.id, {"mtbf_hours": None, "mttr_hours": None})
        text = (
            f"#{equipment.id} - {equipment.name} | Local: {equipment.location} | "
            f"MTBF: {data['mtbf_hours']}h | MTTR: {data['mttr_hours']}h"
        )
        pdf.drawString(40, y, text)
        y -= 18
        if y < 50:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 10)

    pdf.save()
    stream.seek(0)
    return stream


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///maintenance.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.post("/equipments")
    def create_equipment():
        payload = request.get_json(force=True)
        equipment = Equipment(
            name=payload["name"],
            category=payload["category"],
            serial_number=payload["serial_number"],
            location=payload["location"],
        )
        db.session.add(equipment)
        db.session.commit()
        return jsonify({"id": equipment.id}), 201

    @app.get("/equipments")
    def list_equipments():
        rows = Equipment.query.order_by(Equipment.id).all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "serial_number": item.serial_number,
                    "location": item.location,
                }
                for item in rows
            ]
        )

    @app.post("/preventive-plans")
    def create_preventive_plan():
        payload = request.get_json(force=True)
        plan = PreventivePlan(
            equipment_id=payload["equipment_id"],
            frequency_days=payload["frequency_days"],
            next_due_date=datetime.fromisoformat(payload["next_due_date"]).date(),
            activities=payload["activities"],
            active=payload.get("active", True),
        )
        db.session.add(plan)
        db.session.commit()
        return jsonify({"id": plan.id}), 201

    @app.get("/preventive-plans")
    def list_preventive_plans():
        rows = PreventivePlan.query.order_by(PreventivePlan.id).all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "equipment_id": item.equipment_id,
                    "frequency_days": item.frequency_days,
                    "next_due_date": item.next_due_date.isoformat(),
                    "activities": item.activities,
                    "active": item.active,
                }
                for item in rows
            ]
        )

    @app.post("/corrective-records")
    def create_corrective_record():
        payload = request.get_json(force=True)
        failure_start = parse_iso_datetime(payload["failure_start"])
        repair_end = parse_iso_datetime(payload["repair_end"])

        if repair_end < failure_start:
            return jsonify({"error": "repair_end must be later than failure_start"}), 400

        record = CorrectiveRecord(
            equipment_id=payload["equipment_id"],
            description=payload["description"],
            failure_start=failure_start,
            repair_end=repair_end,
            root_cause=payload["root_cause"],
            actions_taken=payload["actions_taken"],
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"id": record.id}), 201

    @app.get("/corrective-records")
    def list_corrective_records():
        equipment_id = request.args.get("equipment_id", type=int)
        query = CorrectiveRecord.query.order_by(CorrectiveRecord.failure_start)
        if equipment_id:
            query = query.filter(CorrectiveRecord.equipment_id == equipment_id)

        rows = query.all()
        return jsonify(
            [
                {
                    "id": item.id,
                    "equipment_id": item.equipment_id,
                    "description": item.description,
                    "failure_start": item.failure_start.isoformat(),
                    "repair_end": item.repair_end.isoformat(),
                    "root_cause": item.root_cause,
                    "actions_taken": item.actions_taken,
                }
                for item in rows
            ]
        )

    @app.get("/indicators")
    def get_indicators():
        equipment_id = request.args.get("equipment_id", type=int)
        query = CorrectiveRecord.query
        if equipment_id:
            query = query.filter(CorrectiveRecord.equipment_id == equipment_id)
            indicators = calculate_indicators(query.all())
            return jsonify({"equipment_id": equipment_id, **indicators})

        equipment_ids = [item[0] for item in db.session.query(CorrectiveRecord.equipment_id).group_by(CorrectiveRecord.equipment_id).all()]
        result = []
        for eq_id in equipment_ids:
            records = CorrectiveRecord.query.filter(CorrectiveRecord.equipment_id == eq_id).all()
            result.append({"equipment_id": eq_id, **calculate_indicators(records)})
        return jsonify(result)

    @app.get("/reports/pdf")
    def report_pdf():
        equipments = Equipment.query.order_by(Equipment.id).all()
        indicators = {}
        for equipment in equipments:
            records = CorrectiveRecord.query.filter(CorrectiveRecord.equipment_id == equipment.id).all()
            indicators[equipment.id] = calculate_indicators(records)

        pdf_stream = create_pdf_report(equipments, indicators)
        return send_file(
            pdf_stream,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="relatorio_manutencao.pdf",
        )

    @app.get("/health")
    def health():
        count = db.session.query(func.count(Equipment.id)).scalar()
        return jsonify({"status": "ok", "equipments": count})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
