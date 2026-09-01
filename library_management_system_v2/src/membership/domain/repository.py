from abc import abstractmethod

from shared.base_repo import Repository


class IMembershipRepository(Repository):
    @abstractmethod
    def block_member_id(self, member_id):
        ...
    
    @abstractmethod
    def unblock_member_by_id(self, member_id):
        ...
        
    @abstractmethod    
    def get_member_by_id(self, member_id):
        ...