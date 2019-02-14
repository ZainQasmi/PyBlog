from main import app
import unittest

class FlaskTestCase(unittest.TestCase):
    # Ensure that Flask was set up correctly
    def test_index_page(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure page 404 works
    def test_404_page(self):
        tester = app.test_client(self)
        response = tester.get('/404', content_type='html/text')
        self.assertTrue('What you were looking for is just not there.' in response.data)

    # Ensure About page works
    def test_about_page(self):
        tester = app.test_client(self)
        response = tester.get('/about', content_type='html/text')
        self.assertTrue('About Us' in response.data)

    # Ensure articles works
    def test_articles_page(self):
        tester = app.test_client(self)
        response = tester.get('/articles', content_type='html/text')
        self.assertTrue('Articles' in response.data)

    # ensure login works
    def test_login(self):
        tester = app.test_client(self)
        response = tester.post(
            '/login',
            data=dict(username="admin",password="admin"),
            follow_redirects=True
        )
        self.assertIn('You are now logged in', response.data)

    # Ensure logout behaves correctly
    def test_logout(self):
        tester = app.test_client(self)
        response = tester.post(
            '/login',
            data=dict(username="admin",password="admin"),
            follow_redirects=True
        )
        response = tester.get('/logout', follow_redirects=True)
        self.assertIn('You are now logged out', response.data)

    # ensure dashboard works
    def test_dash(self):
        tester = app.test_client(self)
        response = tester.post(
            '/login',
            data=dict(username="admin",password="admin"),
            follow_redirects=True
        )
        response = tester.get('/dashboard', content_type='html/text')
        self.assertIn('Dashboard', response.data)

    # ensure add article works
    def test_add_article(self):
        tester = app.test_client(self)
        response = tester.post(
            '/login',
            data=dict(username="admin",password="admin"),
            follow_redirects=True
        )
        response = tester.get('/dashboard', content_type='html/text')
        response = tester.get('/add_article', content_type='html/text')
        self.assertIn('Add Article', response.data)


    # ensure login via google works
    # Python unittests does not support external links
    # ensure login via facebook works
    # Python unittests does not support external links


suite = unittest.TestLoader().loadTestsFromTestCase(FlaskTestCase)
unittest.TextTestRunner(verbosity=2).run(suite)