__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .college import College

from .fellowship import Fellowship

from .nomination import (
    FellowshipNomination,
    FellowshipNominationComment,
    FellowshipNominationEvent,
    FellowshipNominationVotingRound,
    FellowshipNominationVote,
    FellowshipNominationDecision,
    FellowshipInvitation,
)

from .potential_fellowship import PotentialFellowship, PotentialFellowshipEvent
