# Testing Game Abyss

## Introduction

I believe testing is part of telling a good product story, so I combined manual checks with automated coverage throughout development. Each release cycle repeated the same rhythm: write code, run the automated suite, then explore the site like a real player.

## Manual Testing

I kept a living checklist of manual scenarios and repeated them whenever a feature changed:

1. **Account flow**
    - Create a new player account through the sign-up page.
    - Confirm the verification email and log in with the new credentials.
    - Trigger the password reset flow to confirm the email arrives and the new password works.
2. **Staff administration**
    - Log in as a staff member, visit the Jazzmin-styled admin, and confirm I can add, edit, and delete blog posts and gallery items.
    - Approve and unpublish content from the moderation list to check permissions.
3. **Blog authoring**
    - Draft a post with Django Summernote, save it, reopen it, apply formatting, and publish it.
    - Edit the post title and body, then delete it to confirm the success and warning messages appear correctly.
4. **Gallery management**
    - Upload a new image through the gallery form, confirm Cloudinary stores it, and view the resized thumbnail on the front end.
    - Remove the gallery item to ensure orphaned media is cleaned up.
5. **Responsive layout**
    - Resize the browser, test the navigation drawer on tablet widths, and scroll the hero sections on mobile to confirm there is no horizontal overflow.
6. **Contact and informational pages**
    - Submit the contact form with valid and invalid data to confirm both validation messages and SendGrid email delivery.
7. **Accessibility spot checks**
    - Navigate the main pages using only the keyboard and confirm focus states are visible.

## Automated Testing

The repository includes unit tests that cover the core building blocks:

- **Model tests** make sure slugs, timestamps, and publication states behave as expected.
- **View tests** verify that key pages return the right status codes and respect permissions for staff-only routes.
- **Form tests** ensure validation logic displays the right error messages and rejects malformed submissions.

I run these tests locally before each deployment to catch regressions early.

## Real User Testing

Beyond my own scripts, I invited both staff moderators and regular community members to play with preview builds. They created content, tried to break forms, and even stress-tested pagination. Their notes directly influenced copy tweaks, button placements, and confirmation dialogs.

## Browser and Device Coverage

To be confident in the responsive design, I tested the deployed site on:

- **Browsers**: Google Chrome, Mozilla Firefox, and Microsoft Edge (current stable versions).
- **Devices**: a 27" desktop monitor, a 13" laptop, an iPad tablet, and a Pixel and iPhone-sized mobile viewport using device simulators.

## Bug Fixing

Testing did uncover issues—misaligned buttons on mobile, a missing success alert after deleting posts, and a permissions check that was too strict. Each bug went through the same loop: reproduce, write or adjust a test if possible, fix the code, rerun the suite, and record the change in the project notes.

## Final Result

After all rounds of manual, automated, and real-user testing, every core feature—authentication, blogging, gallery uploads, and page browsing—operates smoothly in production. I continue to keep the test checklist handy so future updates enjoy the same level of confidence.
