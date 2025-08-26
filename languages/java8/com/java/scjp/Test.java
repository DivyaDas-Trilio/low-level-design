package com.java.scjp;
import com.java.pack2.Animal;

public class Test {
    public static void main(String[] args) {
        System.out.println("Package Test Demo...");
        Animal a = new Animal();
        System.out.println((a.getClass().getName()));
    }
}
