package JavaCollections;

import java.util.ArrayList;

public class Searching {
   public static void main(String[] args) throws Exception{
    ArrayList al = new ArrayList<>();
    for(int i =1;i<=100000000;i++){
        al.add(i);
    }
    //System.out.println(al);
    System.out.println("searching...");
    System.out.println(al.contains(100000000));
   }
}
