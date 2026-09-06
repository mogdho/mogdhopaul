/* ===================================================
   Mogdho Paul — Portfolio  ·  Scripts
   Scroll reveals + typing effect + icon init
   =================================================== */

document.addEventListener('DOMContentLoaded', () => {



  // ---------- Typing / Role Rotation Effect ----------
  const roles = [
    'Video Editor & Motion Designer',
    'YouTube Content Specialist',
    'Podcast Shorts Editor',
    'Web Developer',
    'SEO Expert',
  ];

  const typingElement = document.getElementById('typing-role');
  let roleIndex = 0;
  let charIndex = 0;
  let isDeleting = false;
  const typeSpeed = 70;
  const deleteSpeed = 40;
  const pauseAfterType = 2000;
  const pauseAfterDelete = 400;

  function typeRole() {
    if (!typingElement) return;

    const currentRole = roles[roleIndex];

    if (!isDeleting) {
      // Typing forward
      typingElement.textContent = currentRole.substring(0, charIndex + 1);
      charIndex++;

      if (charIndex === currentRole.length) {
        // Finished typing — pause, then start deleting
        isDeleting = true;
        setTimeout(typeRole, pauseAfterType);
        return;
      }
      setTimeout(typeRole, typeSpeed);
    } else {
      // Deleting
      typingElement.textContent = currentRole.substring(0, charIndex - 1);
      charIndex--;

      if (charIndex === 0) {
        // Finished deleting — move to next role
        isDeleting = false;
        roleIndex = (roleIndex + 1) % roles.length;
        setTimeout(typeRole, pauseAfterDelete);
        return;
      }
      setTimeout(typeRole, deleteSpeed);
    }
  }

  // Kick off the typing effect
  setTimeout(typeRole, 1000);

  // ---------- Scroll Reveal (IntersectionObserver) ----------
  const revealElements = document.querySelectorAll('.reveal');

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target); // animate once
        }
      });
    },
    {
      threshold: 0.15,
      rootMargin: '0px 0px -40px 0px',
    }
  );

  revealElements.forEach((el) => revealObserver.observe(el));

  // ---------- Smooth Scroll for "Scroll down" ----------
  const scrollIndicator = document.getElementById('scroll-indicator');
  if (scrollIndicator) {
    scrollIndicator.addEventListener('click', () => {
      const aboutSection = document.getElementById('about');
      if (aboutSection) {
        aboutSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
    scrollIndicator.style.cursor = 'pointer';
  }

  // ---------- Hide scroll indicator on scroll ----------
  let scrollHidden = false;
  window.addEventListener('scroll', () => {
    if (!scrollHidden && window.scrollY > 100) {
      scrollHidden = true;
      if (scrollIndicator) {
        scrollIndicator.style.opacity = '0';
        scrollIndicator.style.transition = 'opacity 0.5s ease';
      }
    }
  }, { passive: true });

});
