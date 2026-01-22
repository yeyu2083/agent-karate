package examples.users;

import com.intuit.karate.junit5.Karate;

public class UsersTest {
    
    @Karate.Test
    Karate testUsers() {
        return Karate.run("users").relativeTo(getClass());
    }
    
    @Karate.Test
    Karate testUsersSmoke() {
        return Karate.run("users")
                .tags("@smoke")
                .relativeTo(getClass());
    }
    
    @Karate.Test
    Karate testUsersRegression() {
        return Karate.run("users")
                .tags("@regression")
                .relativeTo(getClass());
    }
}
