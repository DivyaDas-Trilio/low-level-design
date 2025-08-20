class Array {
    public static void main(String[] args) {
        // Single Dimension Array.
        int[] x = new int[5];
        for(int i=0; i<5;i++) x[i] = i;

        for(int i=0;i<5;i++)
            System.out.println(x[i]);

        // 2-Dimension Array
        int[][] y = new int[5][3];
        for(int i=0;i<5;i++){
            for(int j=0;j<3;j++)
                y[i][j] = j;
        }

        for(int i=0;i<5;i++)
            for(int j=0; j<3;j++)
                System.out.println(y[i][j]);

        //Hashcode of object of x[0] is not same as memory address unlike in python's id() method.
        System.out.println(y[0]);
        System.out.println(System.identityHashCode(y));
        System.out.println(System.identityHashCode(y[0]));
        System.out.println(System.identityHashCode(y[1]));

        System.out.println(y.length);
        String[] str = {"A", "B", "C"};
        // length attribute belongs to Array, but length() method belongs to String.
        System.out.println("ABCD".length());

        System.out.println(x);
    }
}
