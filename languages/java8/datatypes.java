class DataType {
    public static void main(String[] args){
        // Primitive Types in java
        // Integral Types ---- FloatingPoint Types
        // byte, short, int, long --- float, double --- char
        // By default every integral types are int in nature.
        // Be careful while doing any operations that can lead to Loss of precision.
        byte b = 10; // storing int to byte.
        short s = 20; // storing int to short
        int i = 100; // Ok
        long l = 200L; // Ok
        char ch = 'A'; // OK, char in java should be single quote.
        float f = 10.54F; // ok, Float type.
        double d = 123.456; // By default every floating number is double in nature.
        boolean bool = true; // this can be true | false
        DataType dt = null; // null can be assigned to any refernce variable.


        System.out.println("Byte:- "+b);
        System.out.println(b instanceof Byte);
        System.out.println("Short:- "+s);
        System.out.println("Int:- "+i);
        System.out.println("Long:- "+l);
        System.out.println("Char:- "+ch);
        System.out.println("Float:- "+f);
        System.out.println("Double:- "+d);
        System.out.println("Boolean:- "+bool);
        System.out.println("DataType:- "+dt);
    }
}
