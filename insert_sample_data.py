from app import app, db
from app.models import Delivery, PaymentLog, Refund, Evaluate
from datetime import datetime
import uuid

# Sample data
delivery_data = {
    'delivery_uuid': '9d1c7a0a-2b7a-4b7b-8c4e-4b8baf0c1e22',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'deliver_time': datetime(2026, 1, 5, 10, 0, 0),
    'create_time': datetime(2026, 1, 5, 9, 0, 0)
}

payment_log_data = {
    'payment_uuid': '3a4b3c2d-8d57-4b0f-9c6a-0f4a0f1d2c33',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'payment_methods': 'credit_card',
    'price': 25.50,
    'state': 'paid',
    'create_time': datetime(2026, 1, 4, 14, 21, 10)
}

refund_data = {
    'refund_uuid': '6b2e4f6b-3f12-4d1a-9c0f-7b0a0b1c2d3e',
    'order_uuid': '7e1f0c7d-ef1a-4d87-a5f4-5d31c9c85d4f',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'create_time': datetime(2026, 1, 6, 16, 0, 0)
}

evaluate_data = {
    'evaluate_uuid': '1f2e3d4c-5b6a-7c8d-9e0f-1a2b3c4d5e6f',
    'product_details_uuid': 'dd7660db-700d-4b1a-866a-16e1cd2ee4dd',
    'user_uuid': '55f7d0f9-fba6-4833-b113-8f55e069c5b6',
    'evaluate_txt': '送貨快，包裝完好，味道很好',
    'create_time': datetime(2026, 1, 7, 20, 30, 0)
}

with app.app_context():
    # Insert delivery data
    delivery = Delivery(
        delivery_uuid=uuid.UUID(delivery_data['delivery_uuid']),
        user_uuid=uuid.UUID(delivery_data['user_uuid']),
        order_uuid=uuid.UUID(delivery_data['order_uuid']),
        deliver_time=delivery_data['deliver_time'],
        create_time=delivery_data['create_time']
    )
    db.session.add(delivery)

    # Insert payment log data
    payment_log = PaymentLog(
        payment_uuid=uuid.UUID(payment_log_data['payment_uuid']),
        user_uuid=uuid.UUID(payment_log_data['user_uuid']),
        order_uuid=uuid.UUID(payment_log_data['order_uuid']),
        payment_methods=payment_log_data['payment_methods'],
        price=payment_log_data['price'],
        state=payment_log_data['state'],
        create_time=payment_log_data['create_time']
    )
    db.session.add(payment_log)

    # Insert refund data
    refund = Refund(
        refund_uuid=uuid.UUID(refund_data['refund_uuid']),
        order_uuid=uuid.UUID(refund_data['order_uuid']),
        user_uuid=uuid.UUID(refund_data['user_uuid']),
        create_time=refund_data['create_time']
    )
    db.session.add(refund)

    # Insert evaluate data
    evaluate = Evaluate(
        evaluate_uuid=uuid.UUID(evaluate_data['evaluate_uuid']),
        product_details_uuid=uuid.UUID(evaluate_data['product_details_uuid']),
        user_uuid=uuid.UUID(evaluate_data['user_uuid']),
        evaluate_txt=evaluate_data['evaluate_txt'],
        create_time=evaluate_data['create_time']
    )
    db.session.add(evaluate)

    # Commit all changes
    db.session.commit()

    print("Sample data inserted successfully!")