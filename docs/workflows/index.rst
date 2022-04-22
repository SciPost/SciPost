#########
Workflows
#########


Workflows


***********
Submissions
***********


Submissions processing
======================

.. mermaid::

   flowchart TD
      Submission --> Prescreening
      subgraph Prescreening
          Admissibility
          Plagiarism(Plagiarism check)
	  COI(Conflict of interest checks)
	  PreA(Preassignment of Fellows)
      end
      Admissibility & Plagiarism -->|Fail| DeskReject(Desk rejection)
      Prescreening --> Screening
      Screening --> Adoption(Fellow takes charge)
      Adoption --> Refereeing
      subgraph Refereeing [Refereeing Round]
          RefInv(Refereeing invitations)
	  VetRep(Vetting Reports)
      end
      Refereeing --> Recommendation
      Recommendation -->|Request minor/major revision| Resubmit
      Resubmit --> Refereeing & RecDirect(Direct Recommendation)
      Recommendation & RecDirect --> Vote(Editorial College Vote) --> Accept & AcceptOther(Accept in other Journal) & Reject
      Accept & AcceptOther --> Production
      subgraph Production
          Proofs(Proofs production)
	  ProofsCheck(Proofs checking)
      end
      Production --> Publish
