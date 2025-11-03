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

## Validation

### HTML Validation

I used the official [W3C Markup Validation Service](https://validator.w3.org/) to validate all HTML pages.

| Page                | Validator                                                                                                                                            | Result | Notes                                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| Home                | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2F)                                           | Pass   | No errors or warnings found.                                                                                            |
| About               | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fabout%2F)                                   | Pass   | No errors or warnings found.                                                                                            |
| Contact             | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fcontact%2F)                                 | Pass   | Fixed: Added missing `id` attribute to help text element for proper `aria-describedby` reference in form field.         |
| Blog                | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fblog%2F)                                    | Pass   | No errors or warnings found.                                                                                            |
| Gallery             | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fgallery%2F)                                 | Pass   | No errors or warnings found.                                                                                            |
| New Post            | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fblog%2Fnew%2F)                              | Pass   | Requires authentication. No errors or warnings found.                                                                   |
| Login               | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Faccounts%2Flogin%2F)                        | Pass   | No errors or warnings found.                                                                                            |
| Sign Up             | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Faccounts%2Fsignup%2F)                       | Pass   | No errors or warnings found.                                                                                            |
| Password Reset      | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Faccounts%2Fpassword%2Freset%2F)            | Pass   | No errors or warnings found.                                                                                            |
| Password Reset Done | [HTML Validator](https://validator.w3.org/nu/?doc=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Faccounts%2Fpassword%2Freset%2Fdone%2F)     | Pass   | No errors or warnings found.                                                                                            |

**Note:** All pages were validated while deployed on Heroku. The W3C validator checks the rendered HTML output, including dynamically generated content from Django templates.

---

### CSS Validation

I used the official [W3C CSS Validation Service](https://jigsaw.w3.org/css-validator/) to validate all CSS files.

| File       | Validator                                                                                                                                       | Result | Notes                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------ |
| style.css  | [CSS Validator](https://jigsaw.w3.org/css-validator/validator?uri=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fstatic%2Fcss%2Fstyle.css) | Pass   | No errors found. Warnings related to CSS variables and vendor prefixes are expected and acceptable. |
| email.css  | [CSS Validator](https://jigsaw.w3.org/css-validator/validator?uri=https%3A%2F%2Fgame-abyss-a25a8ac090c2.herokuapp.com%2Fstatic%2Fcss%2Femail.css) | Pass   | No errors or warnings found. |

**Note:** Both CSS files were validated from the deployed Heroku instance to ensure proper URL encoding and static file serving.

---

### Accessibility Testing (WAVE)

I used the [WAVE (Web Accessibility Evaluation Tool)](https://wave.webaim.org/) browser extension for Chrome to test the accessibility of the deployed site.

**Test Details:**
- **Tool:** WAVE Extension for Chrome
- **URL Tested:** [https://game-abyss-a25a8ac090c2.herokuapp.com/](https://game-abyss-a25a8ac090c2.herokuapp.com/)
- **Date:** November 2025

**Results:**
- ✅ **Zero Errors** - No accessibility errors detected
- ✅ **Proper ARIA Labels** - All interactive elements have appropriate labels
- ✅ **Semantic HTML** - Correct use of heading hierarchy and landmarks
- ✅ **Contrast Compliance** - All text meets WCAG contrast requirements
- ✅ **Keyboard Navigation** - All interactive elements are keyboard accessible
- ⚠️ **Minor Alerts** - Some redundant links and very small text badges (expected for design elements)

![WAVE Accessibility Test Results](documentation/validation/wave.png)

**Key Achievements:**
- No critical accessibility issues
- All form fields properly labeled
- Navigation is fully keyboard accessible
- Color contrast meets WCAG AA standards
- Screen reader friendly structure

---

### Python Code Quality

I used [Pylint](https://pylint.pycqa.org/) to check all Python code quality and ensure best practices were followed.

#### Pylint Score: 10.00/10

The codebase achieved a **perfect score of 10.00/10**, demonstrating excellent code quality and clean structure.

**Result:** `Your code has been rated at 10.00/10`

![Pylint Test Results](documentation/validation/pylint-tests.png)

The screenshot shows multiple runs across all modules (accounts, blog, pages, gallery, core, manage.py), each scoring a perfect **10.00/10**.

#### Django Check

Django's built-in system check framework validates models, URLs, settings, and configurations.

```bash
python manage.py check
```

**Result:** `System check identified no issues (0 silenced).`

#### Automated Tests

All unit and integration tests pass successfully:

```bash
python manage.py test accounts blog pages
```

**Result:**
- **76/76 tests passing** (100% success rate)
- Coverage includes models, views, forms, signals, and permissions
- Test database preserved for faster subsequent runs

**Test Categories:**
- Account management and authentication flows
- Blog post creation, editing, deletion, and permissions
- Comment system with moderation features
- Contact form validation and submission
- Profile management and email verification
- Permission-based access control for staff/superuser actions

#### Flake8 (PEP 8 Style Guide)

Code style checked with [Flake8](https://flake8.pycqa.org/) for PEP 8 compliance:

```bash
python -m flake8 blog accounts pages gallery core --exclude=migrations --max-line-length=100
```

**Result:** 2 minor warnings (ignorable - one is an intentional signal import, the other a documentation line length)

---

## Final Result

After all rounds of manual, automated, and real-user testing, every core feature—authentication, blogging, gallery uploads, and page browsing—operates smoothly in production. I continue to keep the test checklist handy so future updates enjoy the same level of confidence.
