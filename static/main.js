/**
 * On DOMCOntentLoad, run mobile menu functionality
 */
document.addEventListener("DOMContentLoaded", function () {
  // get the mobile menu button and menu
  const mobileMenuButton = document.querySelector(".mobile-menu-button");
  const mobileMenu = document.querySelector("#mobile-menu");

  // get the icons inside the button
  const menuIcon = mobileMenuButton.querySelector(".block");
  const closeIcon = mobileMenuButton.querySelector(".hidden");

  // toggle menu visibility and icon state
  if (mobileMenuButton && mobileMenu) {
    // click event listener for mobileMenuButton
    mobileMenuButton.addEventListener("click", function () {
      // toggles CSS classes
      mobileMenu.classList.toggle("hidden");
      menuIcon.classList.toggle("hidden");
      closeIcon.classList.toggle("hidden");

      const isExpanded =
        mobileMenuButton.getAttribute("aria-expanded") === "true";
      mobileMenuButton.setAttribute("aria-expanded", !isExpanded);
    });
  }
});
