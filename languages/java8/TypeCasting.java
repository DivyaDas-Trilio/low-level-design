import java.util.ArrayList;

public class TypeCasting {
    public static void main(String[] args) {
        ArrayList<String> l = new ArrayList<String>();
        l.add("hi");
        String s = l.get(0);
        System.out.println(s);

        byte b = 128;
        System.out.println(b);
    }

}
