public class SwitchCase {
    public static void main(String[] args) {
        String[] months = {"Jan", "Feb", "May", "July", "Dec"};
        for(String month: months){
        switch (month) {
            case "Jan":
                System.out.println("January.");
                break;
            case "Feb":
                System.out.println("February");
            default:
                System.out.println("No values.");
                break;
            }
        }
    }
    
}
