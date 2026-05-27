public class WithGIL {
    public static void main(String[] args) {
        WithGIL.cpuBoundTask(10000000000.0);
    }

    public static void cpuBoundTask(double num){
        while(num != 0){
            num -= 1;
        }
    }
}
