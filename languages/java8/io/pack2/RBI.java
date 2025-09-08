package io.pack2;

import io.pack1.IBank;

public interface RBI extends IBank{

    void transferUsingUPI(double amount);
}
