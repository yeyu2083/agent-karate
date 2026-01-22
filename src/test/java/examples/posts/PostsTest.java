package examples.posts;

import com.intuit.karate.junit5.Karate;

public class PostsTest {
    
    @Karate.Test
    Karate testPosts() {
        return Karate.run("posts").relativeTo(getClass());
    }
    
    @Karate.Test
    Karate testPostsSmoke() {
        return Karate.run("posts")
                .tags("@smoke")
                .relativeTo(getClass());
    }
}
