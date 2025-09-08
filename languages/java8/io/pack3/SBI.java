package io.pack3;

import io.pack2.RBI;

public class SBI implements RBI{

    private String accountHolderName;
    private String accountId;
    private String accountHolderAge;
    
    SBI(String accountHolderName, String accountHolderAge){
        this.accountHolderName = accountHolderName;
        this.accountHolderAge = accountHolderAge;
    }

    public void transferUsingUPI(double amount){
        System.out.println("Transfer Initiated By User Name:- "+ this.accountHolderName);
        System.out.println("Transferring using UPI... Account Id:"+ this.accountId + "with Amount: " + amount);
    }

    public void withdrawMoney(double amount){
        System.out.println("Withdrawing using..."+ amount);
    }

    public void depositMoney(double amount){
        System.out.println("Deposit Amount "+amount);
    }

    public void transferMoney(double amount){
        System.out.println("Transfer Amount "+  amount);
    }

}
