# Generated by Django 3.2.16 on 2022-11-23 19:23

from django.db import migrations


# Copy the model constants here since they are not imported by apps.get_model:
EIC_ASSIGNED = "assigned"
AWAITING_RESUBMISSION = "awaiting_resubmission"
IN_REFEREEING = "in_refereeing"
REFEREEING_IN_PREPARATION = "refereeing_in_preparation"
VOTING_IN_PREPARATION = "voting_in_preparation"
IN_VOTING = "in_voting"
UNASSIGNED = "unassigned"
SCREENING = "screening"
FAILED_PRESCREENING = "failed_pre"
PRESCREENING_FAILED = "prescreening_failed"
SCREENING_FAILED = "screening_failed"
ASSIGNMENT_FAILED = "assignment_failed"
ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE = "puboffer_waiting"
ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE = "accepted_alt_puboffer_waiting"
ACCEPTED = "accepted"
ACCEPTED_IN_TARGET = "accepted_in_target"
ACCEPTED_IN_ALTERNATIVE = "accepted_alt"

# INCOMING = "incoming"
# PRESCREENING = "prescreening"
REFEREEING_CLOSED = "refereeing_closed"
# RESUBMITTED = "resubmitted"
# AWAITING_DECISION = "awaiting_decision"
# REJECTED = "rejected"
# WITHDRAWN = "withdrawn"
# PUBLISHED = "published"

DECISION_FIXED = "decision_fixed"
REPORT_MINOR_REV, REPORT_MAJOR_REV = -1, -2

# EICRecommendation
VOTING_IN_PREP, PUT_TO_VOTING = (
    "voting_in_prep",
    "put_to_voting",
)

# EditorialDecision
DEPRECATED = -1


def update_submission_status(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")
    EICRecommendation = apps.get_model("submissions", "EICRecommendation")
    EditorialDecision = apps.get_model("submissions", "EditorialDecision")

    # Deal with EIC_ASSIGNED status first:
    eic_assigned = Submission.objects.filter(status=EIC_ASSIGNED)

    # Repair case where rev required but (wrongly) still open for reporting:
    eic_assigned.filter(
        eicrecommendations__status=DECISION_FIXED,
        eicrecommendations__recommendation__in=[
            REPORT_MINOR_REV,
            REPORT_MAJOR_REV,
        ],
    ).filter(open_for_reporting=True).update(open_for_reporting=False)

    # Repair case where open for reporting but no cycle
    eic_assigned.filter(
        open_for_reporting=True
    ).filter(refereeing_cycle="").update(open_for_reporting=False)

    # Repair case where voting in prep but open for reporting
    eic_assigned.filter(open_for_reporting=True).filter(
        id__in=[ r.submission.id for r in EICRecommendation.objects.filter(
            status=VOTING_IN_PREP)]
    ).update(open_for_reporting=False)

    # Repair case where EiC is assigned, but not in set of revreq,
    # open, nocycle, votingprep or voting: give status REFEREEING_CLOSED
    eic_assigned.exclude(
        eicrecommendations__status=DECISION_FIXED,
        eicrecommendations__recommendation__in=[
            REPORT_MINOR_REV,
            REPORT_MAJOR_REV,
        ],
    ).exclude(open_for_reporting=True).exclude(refereeing_cycle="").exclude(
        id__in=[ r.submission.id for r in EICRecommendation.objects.filter(
            status__in=[VOTING_IN_PREP, PUT_TO_VOTING])]
    ).update(status=REFEREEING_CLOSED)

    # Done with repairs.

    # Now define handy querysets and update statuses:
    eic_assigned_revreq = eic_assigned.filter(
        eicrecommendations__status=DECISION_FIXED,
        eicrecommendations__recommendation__in=[
            REPORT_MINOR_REV,
            REPORT_MAJOR_REV,
        ],
    )
    eic_assigned_open = eic_assigned.filter(open_for_reporting=True)
    eic_assigned_nocycle = eic_assigned.filter(refereeing_cycle="")
    eic_assigned_votingprep = eic_assigned.filter(
        id__in=[ r.submission.id for r in EICRecommendation.objects.filter(
            status=VOTING_IN_PREP)]
    )
    eic_assigned_voting = eic_assigned.filter(
        id__in=[ r.submission.id for r in EICRecommendation.objects.filter(
            status=PUT_TO_VOTING)]
    )

    if len(eic_assigned) != (
            len(eic_assigned_revreq) + len(eic_assigned_open) +
            len(eic_assigned_nocycle) + len(eic_assigned_votingprep) +
            len(eic_assigned_voting)
    ):
        print("Error: queryset lengths do not match. Aborting.")
        print(f"{len(eic_assigned) = }")
        print(f"{len(eic_assigned_revreq) = }")
        print(f"{len(eic_assigned_open) = }")
        print(f"{len(eic_assigned_nocycle) = }")
        print(f"{len(eic_assigned_votingprep) = }")
        print(f"{len(eic_assigned_voting) = }")
        print(f"{len(eic_assigned_revreq.union(eic_assigned_open, eic_assigned_nocycle, eic_assigned_votingprep, eic_assigned_voting)) = }")
        print(f"{len(eic_assigned_revreq) + len(eic_assigned_open) + len(eic_assigned_nocycle) + len(eic_assigned_votingprep) + len(eic_assigned_voting) = }")
        print(f"{eic_assigned_revreq.intersection(eic_assigned_open) = }")
        print(f"{eic_assigned_revreq.intersection(eic_assigned_nocycle) = }")
        print(f"{eic_assigned_revreq.intersection(eic_assigned_votingprep) = }")
        print(f"{eic_assigned_revreq.intersection(eic_assigned_voting) = }")
        print(f"{eic_assigned_open.intersection(eic_assigned_nocycle) = }")
        print(f"{eic_assigned_open.intersection(eic_assigned_votingprep) = }")
        print(f"{eic_assigned_open.intersection(eic_assigned_voting) = }")
        print(f"{eic_assigned_nocycle.intersection(eic_assigned_votingprep) = }")
        print(f"{eic_assigned_nocycle.intersection(eic_assigned_voting) = }")
        print(f"{eic_assigned_votingprep.intersection(eic_assigned_voting) = }")
        print(f"{eic_assigned.difference(eic_assigned_revreq.union(eic_assigned_open, eic_assigned_nocycle, eic_assigned_votingprep, eic_assigned_voting)) = }")
        raise

    eic_assigned_revreq.update(
        status=AWAITING_RESUBMISSION
    )
    eic_assigned_open.update(
        status=IN_REFEREEING
    )
    eic_assigned_nocycle.update(
        status=REFEREEING_IN_PREPARATION
    )
    eic_assigned_votingprep.update(
        status=VOTING_IN_PREPARATION
    )
    eic_assigned_voting.update(
        status=IN_VOTING
    )

    # Now deal with other cases
    Submission.objects.filter(
        status=UNASSIGNED
    ).update(status=SCREENING)

    Submission.objects.filter(
        status=FAILED_PRESCREENING
    ).update(status=PRESCREENING_FAILED)

    Submission.objects.filter(
        status=ASSIGNMENT_FAILED
    ).update(status=SCREENING_FAILED)

    Submission.objects.filter(
        status=ACCEPTED_AWAITING_PUBOFFER_ACCEPTANCE
    ).update(status=ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE)

    for submission in Submission.objects.filter(status=ACCEPTED):
        decision = EditorialDecision.objects.filter(
            submission__id=submission.id
        ).exclude(status=DEPRECATED).order_by("-version").first()
        if submission.submitted_to == decision.for_journal:
            Submission.objects.filter(pk=submission.id).update(status=ACCEPTED_IN_TARGET)
        else:
            Submission.objects.filter(pk=submission.id).update(status=ACCEPTED_IN_ALTERNATIVE)


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0117_alter_submission_status'),
    ]

    operations = [
        migrations.RunPython(
            update_submission_status, reverse_code=migrations.RunPython.noop
        ),
    ]