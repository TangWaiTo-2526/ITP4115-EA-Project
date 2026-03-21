from app import app, db
from app.models import Delivery, PaymentLog, Refund, Evaluate

with app.app_context():
    print("=== Delivery Records ===")
    deliveries = Delivery.query.all()
    for d in deliveries:
        print(f"UUID: {d.delivery_uuid}, User: {d.user_uuid}, Order: {d.order_uuid}, Deliver Time: {d.deliver_time}, Create Time: {d.create_time}")

    print("\n=== Payment Log Records ===")
    payments = PaymentLog.query.all()
    for p in payments:
        print(f"UUID: {p.payment_uuid}, User: {p.user_uuid}, Order: {p.order_uuid}, Method: {p.payment_methods}, Price: {p.price}, State: {p.state}, Create Time: {p.create_time}")

    print("\n=== Refund Records ===")
    refunds = Refund.query.all()
    for r in refunds:
        print(f"UUID: {r.refund_uuid}, Order: {r.order_uuid}, User: {r.user_uuid}, Create Time: {r.create_time}")

    print("\n=== Evaluate Records ===")
    evaluates = Evaluate.query.all()
    for e in evaluates:
        print(f"UUID: {e.evaluate_uuid}, Product: {e.product_details_uuid}, User: {e.user_uuid}, Text: {e.evaluate_txt}, Create Time: {e.create_time}")