import com.intuit.karate.junit5.Karate;

public class TestRunner {
    
    @Karate.Test
    Karate testAll() {
        return Karate.run().relativeTo(getClass());
    }
    
    @Karate.Test
    Karate testSmoke() {
        return Karate.run()
                .tags("@smoke")
                .relativeTo(getClass());
    }
    
    @Karate.Test
    Karate testRegression() {
        return Karate.run()
                .tags("@regression")
                .relativeTo(getClass());
    }
}
