if __name__ == "__main__":
    from lld.design_patterns.prototype.email import  Email, PremiumEmail
    import pdb; pdb.set_trace()
    # Create an original email
    e1 = Email("Hello!", "This is the body of the email.",
                           "dj@gmail.com", "support@gmail.com")
    e4 = PremiumEmail("Hello!", "This is the body of the email.",
                           "dj@gmail.com", "support@gmail.com", priority="High")
    
    # e2 = Email()
    
    
    # Naive Approvach to copy objects is via getters and setters.
    # e2.subject = e1.subject
    # e2.body = e1.body
    # e2.sender = e1.sender
    # e2.recipient = e1.recipient
    
    e2 = e1.clone()
    e3 = e1.clone()
    e5 = e4.clone()
    
    print(e1)
    print(e2)
    print(e3)
    print(e4)
    print(e5)
