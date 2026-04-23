from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from marketplace.models import ProducerProfile, ProducerSubOrder, Settlement


def build_weekly_settlement(producer: ProducerProfile) -> Settlement:
    today = timezone.localdate()
    week_end = today
    week_start = today - timedelta(days=6)
    delivered = ProducerSubOrder.objects.filter(
        producer=producer,
        status='delivered',
        updated_at__date__range=[week_start, week_end],
    )
    totals = delivered.aggregate(subtotal=Sum('subtotal'), payout=Sum('producer_payout'))
    subtotal = totals['subtotal'] or 0
    payout = totals['payout'] or 0
    commission = subtotal - payout
    settlement, _ = Settlement.objects.update_or_create(
        producer=producer,
        week_start=week_start,
        week_end=week_end,
        defaults={
            'orders_total': subtotal,
            'commission_total': commission,
            'payout_total': payout,
            'status': 'processed',
        },
    )
    return settlement
