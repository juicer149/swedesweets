from __future__ import annotations

from django.shortcuts import render

from ops_portal.dashboard.actions import build_dashboard_actions
from ops_portal.dashboard.queues import build_dashboard_queues


def index(request):
    dashboard_actions = build_dashboard_actions(
        account_role=request.account_role,
        role_spec=request.role_spec,
    )
    dashboard_queues = build_dashboard_queues(
        account_role=request.account_role,
        role_spec=request.role_spec,
    )

    return render(
        request,
        "ops_portal/dashboard/index.html",
        {
            "dashboard_actions": dashboard_actions,
            "dashboard_queues": dashboard_queues,
        },
    )
