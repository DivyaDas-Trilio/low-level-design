public class Operators {
    public static void main(String[] args) {
        int a = 10;
        // Pre Increment/Decrement Operator
        System.out.println(++a); // first increase then print
        System.out.println(--a); // first decrease then print

        // post Increment/Decrement Operator
        System.out.println(a++); // first print then increase
        System.out.println(a--); // first print then decrease

        // latest value
        System.out.println(a);

        // Arithmetic Operators +, -, *, /, %
        int n1 = 10, n2=20;
        System.out.println(n1+n2);
        System.out.println(n2-n1);
        System.out.println(n2/n1);
        System.out.println(n1*n2);
        System.out.println(n1%n2);

        // priority and precedence, + - , * / %


        // Concatenation Operator
        System.out.println("10"+"20"); // for efficiency use StringBuilder
        System.out.println(10+"20");
        int[] n3 = {10};
        int[] n4 = {20};
        // System.out.println(n3+n4); Not supported.

        // Relational Operator, > >= < <= == !=

        // Logical operators, &&, ||, !, ^

        // Assignment Operator, =

        // Ternary Operator ? :
    }
    
}
