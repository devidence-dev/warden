class ApprovalNotFoundError(Exception):
    def __init__(self, approval_id: str):
        self.approval_id = approval_id
        super().__init__(f"Approval {approval_id} not found")


class ApprovalAlreadyResolvedError(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(f"Approval is already {status}")
