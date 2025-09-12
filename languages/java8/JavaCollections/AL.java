package JavaCollections;

import java.util.*;

class AL {
    public static void main(String[] args) {
        ArrayList<Object> al = new ArrayList(10);
        al.add(10);
        for(int i=0; i<20;i++){
            al.add("Hello");
        }
        for(Object i : al){
            System.out.println(i);
        }
        ArrayList<Object> all = new ArrayList(10);
        all.addAll(al);

        al.clear();
        
        System.out.println(al); 
        System.out.println(all); 


    }
}
