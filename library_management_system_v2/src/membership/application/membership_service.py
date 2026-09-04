from shared.ids import MemberId
from shared.exceptions import EntityAlreadyExistsError
from membership.domain.member import Member
from membership.domain.email import EmailAddress
from membership.domain.repository import IMembershipRepository


class MembershipService:
    """Application service for the Membership subdomain — thin CRUD/lifecycle.

    No domain service (supporting subdomain). Depends on the repository INTERFACE.
    """

    def __init__(self, repo: IMembershipRepository):
        self._membership_repo = repo

    def get_member(self, member_id: MemberId) -> Member:
        return self._membership_repo.get(member_id)

    # UC-10: register (uniqueness checked here, against the email business key)
    def register_member(self, name: str, email: str) -> MemberId:
        email_vo = EmailAddress(email)                                  # format validation (VO)
        if self._membership_repo.exists_email(email_vo.value):          # uniqueness → pass the STRING
            raise EntityAlreadyExistsError(f"email {email_vo.value} already exists.")
        member = Member.register(name=name, email=email_vo)
        self._membership_repo.save(member)
        return member.id                                               # return the new id

    # UC-10: remove == delete (blocking is a separate operation)
    def remove_member(self, member_id: MemberId) -> None:
        self._membership_repo.delete(member_id)

    def update_member_profile(self, member_id: MemberId, *,
                              name: str | None = None, email: str | None = None) -> None:
        member = self._membership_repo.get(member_id)                  # load
        email_vo = EmailAddress(email) if email is not None else None
        member.update_profile(name=name, email=email_vo)               # domain command
        self._membership_repo.save(member)                             # save

    def block_member(self, member_id: MemberId) -> None:
        member = self._membership_repo.get(member_id)
        member.block()
        self._membership_repo.save(member)

    def unblock_member(self, member_id: MemberId) -> None:
        member = self._membership_repo.get(member_id)
        member.unblock()
        self._membership_repo.save(member)
