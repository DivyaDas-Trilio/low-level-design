class  Student{
    static String school_name = "HIT"; 
    
}

class Main{
    public static void main(String[] args) {
        Student s1 = new Student();
        Student s2 = new Student();

        System.out.println(Student.school_name);
        System.out.println(s1.school_name);
        System.out.println(s2.school_name);

        // if only one copy is getting created for class var, then id of below should be same.
        System.out.println(System.identityHashCode(s1.school_name));
        System.out.println(System.identityHashCode(s2.school_name));
        System.out.println(System.identityHashCode(Student.school_name));

        Student.school_name = "st.stephens";
        // # if any changes is done on class var, then should be reflected jto all.

        System.out.println(Student.school_name);
        System.out.println(s1.school_name);
        System.out.println(s2.school_name);
    }
}
