 <footer id="footer">
      <div class="container">
        <div class="footer-grid">
          <div class="footer-col">
            <h4 id="i1lrdo">Electro <span id="imn87c">Hub</span>
            </h4>
            <p id="ij3473">Your trusted destination for premium electronics and cutting-edge tech.</p>
          </div>
          <div class="footer-col">
            <h4>Quick Links</h4>
            <a href="#hero">Home</a>
            <a href="#product_showcase">Products</a>
            <a href="#featured_categories">Categories</a>
            <a href="#deals_banner">Deals</a>
          </div>
          <div class="footer-col">
            <h4>Customer Service</h4>
            <a href="#contact">Contact Us</a>
            <a href="#">Shipping Policy</a>
            <a href="#">Returns</a>
            <a href="#">FAQ</a>
          </div>
          <div class="footer-col">
            <h4>Newsletter</h4>
            <p id="ig5sza">Get the latest deals in your inbox.</p>
            <div class="newsletter-input">
              <input type="email" placeholder="Your email" />
              <button type="button">Join</button>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <p>© 2024 ElectroHub. All rights reserved.</p>
        </div>
      </div>
    </footer>
    <script>
      function toggleMenu() {
        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
          navMenu.classList.toggle('active');
        }
      }
      document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
          const navMenu = document.querySelector('.nav-menu');
          if (navMenu) {
            navMenu.classList.remove('active');
          }
        });
      });
    </script>