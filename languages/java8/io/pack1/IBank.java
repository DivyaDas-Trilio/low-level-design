package io.pack1;

public interface IBank {
    public static final float ROI=0.0f;
    void withdrawMoney(double amount);
    void depositMoney(double amount);
    void transferMoney(double amount);
}
