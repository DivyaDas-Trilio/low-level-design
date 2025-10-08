class PopCorn {
    public void taste() {
        System.out.println("Salty");
    }
}

public class InnerClass {
    public static void main(String[] args) {
        PopCorn p = new PopCorn() {
            public void taste() {
                System.out.println("Sweet.");
            }
        };
        p.taste();
    }
}
