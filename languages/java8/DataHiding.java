public class DataHiding {
    private double balance;

    DataHiding(){
        balance = 0.0;
    }

    public double getBalance(){
        return balance;
    }

}


class Main{
    public static void main(String[] args) {
        DataHiding dh = new DataHiding();
        System.out.println(dh.getBalance());
    }
}
