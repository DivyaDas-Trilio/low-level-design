from membership.domain.repository import IMembershipRepository


class InMemoryMembershipRepository(IMembershipRepository):
    def get(self, id):
        ...
        
    def save(self, aggregate) -> None:
        ...    
        
    def block_member_id(self, member_id):
        ...
        
    def unblock_member_by_id(self, member_id):
        ...
        
    def get_member_by_id(self, member_id):
        ...