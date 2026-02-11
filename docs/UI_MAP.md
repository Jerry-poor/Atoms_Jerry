# UI_MAP

Sources:
- `docs/UI documentation task.docx` (primary structured source for components/interactions)
- `docs/atoms_ui_audit_report.docx` (screenshots extracted into `screenshots/`)

Conventions:
- Items marked `UNKNOWN` are unclear or unspecified in the input docs. They must be implemented with the safest minimal behavior.
- Route/component mappings are implementation targets for this repo; UI behavior must match the tables below.

## Page_01_Home (Page 01 - Home)

Purpose: The landing page introduces Atoms, highlights its AI-powered web/app builder features, and guides visitors toward starting a project or learning more about pricing and templates.

Screenshot: `screenshots/page_01_home.png`

Frontend mapping:
- Route: `/`
- Next.js file (planned): `apps/web/app/(marketing)/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Logo | "Atoms" logo | Top left of the header |
| Navigation links | Pricing, Resources (has dropdown), Log in, Sign up | Top right header |
| Hero heading | "Build anything at the speed of thought" with supporting tagline | Center of hero section |
| Search/Start input | Input field with placeholder text for project description and a Start button | Hero section, below main heading |
| Template tabs | Category tabs (All, Website, App, etc.) | Template section below hero |
| Template cards | Cards with template name, description and icons | Template section grid |
| Old vs Atoms comparison | Side-by-side cards describing traditional vs Atoms way plus Try for free button | "Online business, now easier than ever" section |
| AI Team role cards | Cards for roles like Data Analyst, Deep Researcher, etc. | "AI teams at your fingertips" section |
| Feature navigation list | Items like Visual Editor, Backend, Race Mode, Instant AI integrations, SEO agent, More features | Feature section's side menu |
| Feature images | Illustrations demonstrating each feature | To the right of feature navigation |
| Success stories world map | Interactive map with sample success story card and arrows | "Success Stories" section |
| Testimonials | User testimonials in cards with avatars | "Loved by users worldwide" section |
| Pricing preview | Plan cards (Free, Pro, Max) with features and Get Started button | Pricing teaser section |
| FAQ | Accordion of frequently asked questions | Near bottom before final CTA |
| Gradient call-to-action | Section encouraging users to try for free | Above footer |
| Footer | Columns: Product (Templates, Pricing, Docs…), Resources (Blog, Use Cases, Videos, GitHub), About (MetaGPT, Foundation Agents, Terms…), Community (Affiliates, Explorer Program, Help Center, Community links), social icons, language selector | Bottom of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Atoms logo | Navigates back to home page when on other pages |
| Click | Pricing link | Opens the dedicated pricing page (Page_02_Pricing) |
| Hover/Click | Resources | Displays dropdown menu with blog, use-cases, videos, affiliates, explorer program, help center, community |
| Click | Log in | Opens login page (Page_13_Login) |
| Click | Sign up | Opens sign-up page (Page_14_SignUp) |
| Input + click | Search/Start box | User can enter a project description and click Start to begin building (unknown behaviour because it requires account access) |
| Click | Template tabs | Filters template cards by category; clicking a card scrolls or opens details (unknown) |
| Click | Try for free / Get Started buttons throughout page | Navigates to sign-up or pricing depending on context |
| Click | FAQ accordion plus icons | Expands an answer inline |
| Click | Footer links | Navigates to respective pages (e.g., Templates returns to top of home, Blog opens blog home page, GitHub opens external repository) |

Entry/Exit:
- Entry: Visitors arrive via the site root (https://atoms.dev).
- Exit: Main navigation routes to Pricing, Resources pages, log-in/sign-up states, and template categories. Footer links and call-to-action buttons also direct users to pricing, docs, blog, help center, affiliates, explorer program or external community platforms.

## Page_02_Pricing (Page 02 - Pricing)

Purpose: Presents Atoms' subscription plans with a pricing toggle (monthly vs yearly), feature comparison, FAQs and a final sign-up call-to-action.

Screenshot: `screenshots/page_02_pricing.png`

Frontend mapping:
- Route: `/pricing`
- Next.js file (planned): `apps/web/app/(marketing)/pricing/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Header | Same as home (logo, navigation, log-in/sign-up) | Top of page |
| Pricing toggle | Switch between Monthly and Annual billing | Above plan cards |
| Plan cards | Cards for Free, Pro, Max plans; each shows price, description, feature list, and action button (e.g., Get Started) | Main section |
| Feature matrix | Checklist comparing features across plans | Below plan cards |
| FAQ | Accordion listing pricing-specific questions | Near bottom |
| Final CTA | Gradient section with call to action to start building | Above footer |
| Footer | Same as home page | Bottom of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Billing toggle | Switches displayed prices between monthly and annual rates |
| Click | Plan card buttons (Get Started) | Opens sign-up or checkout (unknown without login) |
| Click | FAQ plus icons | Expands/collapses answers inline |
| Click | Navigation/footers | Behave identically to those on home page |

Entry/Exit:
- Entry: From the home page via the Pricing link or from pricing mentions across the site.
- Exit: Users can choose a plan (leading to sign-up), scroll back to home using the logo, or navigate to other resources via the header/footer.

## Page_03_Resources_Dropdown (Page 03 - Resources Dropdown)

Purpose: Provides quick access from the header to various resource pages: Blog, Use Cases, Videos, Affiliates, Explorer Program, Help Center, and Community, along with a highlighted article preview.

Screenshot: `screenshots/page_03_resources_dropdown.png`

Frontend mapping:
- Route: `N/A (header dropdown state)`
- Next.js file (planned): `apps/web/components/site-header.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Overlay background | Dark translucent overlay covering the page | Entire viewport except navigation |
| Menu list | Links: Blog, Use Cases, Videos, Affiliates, Explorer Program, Help Center, Community | Left side of overlay |
| Highlighted article preview | Image thumbnail, title, short excerpt, and Read Article link | Right side of overlay |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Blog | Navigates to blog home page (Page_04_Blog_Home) |
| Click | Use Cases | Opens use-cases page (Page_06_Use_Cases) |
| Click | Videos | Navigates to video library (Page_08_Videos) |
| Click | Affiliates | Opens affiliate program page (Page_09_Affiliate) |
| Click | Explorer Program | Opens explorer program page (Page_10_Explorer_Program) |
| Click | Help Center | Opens help center (Page_11_Help_Center) |
| Click | Community | Likely opens external community/Discord (not fully explored) |
| Click | Highlighted article | Opens the referenced blog post |
| Click outside overlay | Closes the dropdown and returns to current page |  |

Entry/Exit:
- Entry: Triggered by hovering or clicking on the Resources navigation item.
- Exit: Selecting an item navigates to the appropriate page, or clicking outside the overlay closes it and returns to the previous page.

## Page_04_Blog_Home (Page 04 - Blog Home)

Purpose: Serves as the main blog index, featuring a prominent article and a grid of recent posts categorized by tags.

Screenshot: `screenshots/page_04_blog_home.png`

Frontend mapping:
- Route: `/blog`
- Next.js file (planned): `apps/web/app/(marketing)/blog/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Hero heading | "Blog" with subtitle introducing the blog | Top of page |
| Featured article card | Large card with image thumbnail, category tag, title, author/date, Read Article link | Under hero |
| Filter tabs or tag pills | Tags like Product Updates, Community & OpenSource, Tech Insights etc. | Above grid of posts |
| Article cards grid | Multiple cards each with image thumbnail, title, date, and category tag | Main section |
| Pagination or "Load more" | Additional posts appear as user scrolls (infinite scroll behaviour) | Bottom of grid |
| Footer | Same as home page | Bottom |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Featured article / card | Opens the selected blog post (Page_05_Blog_Post) |
| Click | Tag pills | Filters the list to posts matching the selected tag |
| Scroll | Post grid | Loads more posts as you scroll down |
| Click | Navigation/footers | Standard navigation across site |

Entry/Exit:
- Entry: Via the Blog link in the resources dropdown or from article backlinks within posts.
- Exit: Selecting an article opens its detailed page; navigation and footer links provide routes to other pages.

## Page_05_Blog_Post (Page 05 - Blog Post)

Purpose: Displays a single blog article with table of contents, media embeds, quote blocks, and related links.

Screenshot: `screenshots/page_05_blog_post.png`

Frontend mapping:
- Route: `/blog/[slug] (UNKNOWN slug)`
- Next.js file (planned): `apps/web/app/(marketing)/blog/[slug]/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Back link | "All posts" link | Top left above article title |
| Article title & metadata | Title, date, reading time | Top of content |
| Share icons | Icons for sharing to X/Twitter, Instagram, LinkedIn, TikTok | Top right of article |
| Table of contents (TOC) | List of article headings; sticky sidebar | Left of article on wider screens |
| Article body | Rich text with paragraphs, images, blockquotes, headings, code blocks or bullet lists | Main column |
| Embedded video player | Embedded YouTube video | Where included in article |
| End-of-article links | Bulleted list linking to other resources or actions | Bottom of article |
| Footer | Site footer | End of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | All posts | Returns to blog home (Page_04_Blog_Home) |
| Click | TOC entries | Smooth scrolls to corresponding section within the article |
| Click | Share icons | Opens sharing dialogues for respective social networks |
| Click | Embedded video | Plays the video within the page |
| Click | Hyperlinks within article | Navigates to referenced external or internal resources |
| Click | End-of-article bullet links | Navigates to product page (e.g., build an app, Product Hunt listing, Discord) |

Entry/Exit:
- Entry: From blog home or any location linking to an article.
- Exit: Use the back link to return to blog home, select other internal links or follow share/outbound links.

## Page_06_Use_Cases (Page 06 - Use Cases)

Purpose: Showcases dozens of AI-powered generators and tools that can be built using Atoms, organized primarily under the "Website" category with a "Show more" option revealing additional categories.

Screenshot: `screenshots/page_06_use_cases.png`

Frontend mapping:
- Route: `/use-cases`
- Next.js file (planned): `apps/web/app/(marketing)/use-cases/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Hero heading | "Build Your Next Creative Project with AI" with descriptive subtitle | Top of page |
| Call-to-action button | Start Building Now | Below hero text |
| Search/filter navigation | Category tabs or pills (implicitly listing by Website, App etc.) | Under hero |
| Use case cards grid | Numerous cards each with an icon, bold title (e.g., AI Business Card Generator, AI Website Builder, AI HTML Website Builder), and a short description | Main body, forms large grid |
| Show more button | "Show More" reveals further categories and cards | Below initial grid |
| Footer | Standard site footer | Bottom |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Start Building Now | Navigates to sign-up or builder interface (requires account) |
| Click | Use case card | Likely opens a template or pre-filled builder (unknown without login) |
| Click | Show more | Expands the list to display additional categories such as "APP" and "Deep Research" (Page_07_Use_Cases_App) |
| Click | Footer links | Navigate to other sections of the site |

Entry/Exit:
- Entry: From resources dropdown via "Use Cases" or from other pages linking to specific use cases.
- Exit: Users can expand the list, select a specific generator (requiring account access), or navigate to other site sections via header/footer.

## Page_07_Use_Cases_App (Page 07 - Use Cases (APP & Deep Research))

Purpose: After clicking Show More on the use-cases page, additional categories appear such as APP and Deep Research. Each category contains a smaller set of cards for more specialized use cases.

Screenshot: `screenshots/page_07_use_cases_app.png`

Frontend mapping:
- Route: `/use-cases/app (UNKNOWN if separate route)`
- Next.js file (planned): `apps/web/app/(marketing)/use-cases/app/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Category headings | APP, Deep Research | Above each group of cards |
| App use-case cards | Examples: Smart Flashcard App, App & Website Builder | Under APP heading |
| Deep Research use-case cards | Examples: AI Business Idea Generator, AI Market Research Agent, AI Startup Idea Validator, AI Business Strategy Generator | Under Deep Research heading |
| Back to top link | Not explicitly provided; users must scroll back | Top of page or via browser controls |
| Footer | Standard site footer | Very bottom |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Individual use-case cards | Would open their respective generators/templates (requires login) |
| Scroll | Page scroll | Allows user to return to upper categories |
| Click | Footer links | Navigate to other sections of the site |

Entry/Exit:
- Entry: By clicking "Show More" from the main use-cases page.
- Exit: Scroll back up to earlier categories or navigate via header/footer links.

## Page_08_Videos (Page 08 - Videos)

Purpose: Acts as Atoms' video library, presenting tutorials and feature highlights via a searchable, filterable grid of video cards.

Screenshot: `screenshots/page_08_videos.png`

Frontend mapping:
- Route: `/videos`
- Next.js file (planned): `apps/web/app/(marketing)/videos/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Hero heading | "Videos" with an introductory description about learning how to use Atoms | Top of page |
| Tag filters | Pills such as All, Tutorial, No-code, Step-by-step, etc. | Below hero |
| Video cards grid | Each card shows a thumbnail image with a play button overlay, the video title and a set of tags | Main section |
| Footer | Standard site footer | End of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Tag filter | Filters the displayed videos to the selected tag |
| Click | Video card | Opens the corresponding video page or plays the video (unknown without login) |
| Scroll | Video grid | Loads more videos as user scrolls down |
| Click | Footer links | Navigate elsewhere on the site |

Entry/Exit:
- Entry: Via the resources dropdown link labeled "Videos".
- Exit: Users can select a video (opening or requiring login), or navigate away using the header or footer links.

## Page_09_Affiliate (Page 09 - Affiliate Program)

Purpose: Provides information about the Atoms affiliate program, including commission details, step-by-step participation instructions, benefits, and FAQs, and encourages visitors to apply.

Screenshot: `screenshots/page_09_affiliate.png`

Frontend mapping:
- Route: `/affiliate`
- Next.js file (planned): `apps/web/app/(marketing)/affiliate/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Hero banner | Large heading promoting earning commissions with call-to-action button Start Earning | Top of page |
| Three-step process | Cards labelled Apply, Share, Earn with icons and short descriptions | Below hero |
| Testimonials / video | Section with testimonial or promotional video | Mid-page |
| About program | Grid of boxes explaining Commission rate, Cookie period, Promotional Kit, Restrictions, Program Agreement, Payments | After video section |
| Benefits | Icons and descriptions for Fast Payouts, Ethical Promotion, Personalised Support | Lower page |
| FAQ | Accordion questions relating to the affiliate program | Near bottom |
| Final CTA | Gradient section inviting to apply now | Above footer |
| Footer | Standard site footer | End of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Start Earning / Apply Now / Apply button | Navigates to sign-up or application form (likely requires account) |
| Click | Process cards | May link to details about each step (uncertain) |
| Click | FAQ items | Expands answers inline |
| Click | Footer links | Standard navigation to other pages |

Entry/Exit:
- Entry: Via the resources dropdown or community links labelled "Affiliates".
- Exit: Users can apply (leading to sign-in or a form), or navigate to other site pages via header/footer.

## Page_10_Explorer_Program (Page 10 - Explorer Program)

Purpose: Invites power users and early adopters to join the Atoms Explorer Program, outlining benefits, contributions required, and the identity verification process.

Screenshot: `screenshots/page_10_explorer_program.png`

Frontend mapping:
- Route: `/explorer-program`
- Next.js file (planned): `apps/web/app/(marketing)/explorer-program/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Hero heading | "Join the Atoms Explorer Program" with description and Become an Atoms Explorer button | Top of page |
| Benefits grid | Cards such as Priority Access, Verified Identity, Explorer's Journey etc., each with an icon and description | Below hero |
| Contribution journey | Step-by-step list (Be Active, Give Feedback, Share Content) explaining how to contribute | Mid-page |
| Identity activation process | Four-step process describing how identity verification works | Lower section |
| Final call-to-action | Encouraging users to apply | Above footer |
| Footer | Standard site footer | End of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Become an Atoms Explorer / Apply Now | Likely opens an application form (requires login) |
| Click | Benefits or process cards | Possibly reveals more information (not observed) |
| Click | Footer links | Standard navigation |

Entry/Exit:
- Entry: Via resources dropdown (Explorer Program) or community links.
- Exit: Apply button leads to application (requires login); navigation elements allow departure to other sections of the site.

## Page_11_Help_Center (Page 11 - Help Center)

Purpose: Acts as a self-service support portal with step-by-step guides, tutorials, and troubleshooting for Atoms users.

Screenshot: `screenshots/page_11_help_center.png`

Frontend mapping:
- Route: `/help-center`
- Next.js file (planned): `apps/web/app/(marketing)/help-center/page.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Header | Atoms logo linking back to main site, Features link, English language selector | Top of help center site |
| Search bar | "Search articles" input with search icon | Centered hero section |
| Category cards | Large cards labelled Getting Started, Plans & Billing, FAQ, Features, Integrations, Tips & Tricks with article counts | Below search |
| Additional category links | Links for Use Cases, Resources, Terms & Policies | Near bottom |
| Live chat icon | Small chat bubble for contacting support | Bottom right of viewport |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Input | Search bar | Filters articles based on typed keywords |
| Click | Category card | Opens a page listing articles in the selected category |
| Click | Additional category links | Navigates to pages for use cases, resources or policy documents |
| Click | Live chat icon | Opens chat window to contact support |
| Click | Header links | Returns to Atoms main site or changes language |

Entry/Exit:
- Entry: Via Help Center link in resources dropdown or community links, or from within the product.
- Exit: Users can browse support articles, change language, return to Atoms site via the header, or close the help center tab.

## Page_12_404 (Page 12 - 404 Error Page)

Purpose: Handles invalid URLs, informing visitors that the requested page doesn't exist and offering options to refresh or go back to the home page.

Screenshot: `screenshots/page_12_404.png`

Frontend mapping:
- Route: `Next.js not-found`
- Next.js file (planned): `apps/web/app/not-found.tsx`

Backend mapping:
- N/A (static marketing page)

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Illustration | Playful character indicating confusion or lost page | Center of page |
| Error message | Text explaining that the page couldn't be found | Below illustration |
| Buttons | Refresh and Go to Atoms | Under message |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Refresh | Reloads the current URL in case of a transient error |
| Click | Go to Atoms | Redirects to the home page (Page_01_Home) |

Entry/Exit:
- Entry: By navigating to a non-existent path (e.g., /changelog).
- Exit: Use provided buttons to refresh or return home.

## Page_13_Login (Page 13 - Login)

Purpose: Allows existing users to authenticate; the page is also the boundary after which back-end functionality becomes available, so the audit stops here without logging in.

Screenshot: `screenshots/page_13_login.png`

Frontend mapping:
- Route: `/login`
- Next.js file (planned): `apps/web/app/(auth)/login/page.tsx`

Backend mapping:
- `GET /api/auth/oauth/google/start` (DOC: required)
- `GET /api/auth/oauth/github/start` (MANDATORY requirement)
- `GET /api/auth/oauth/{provider}/callback`
- `POST /api/auth/login` (email+password)
- `POST /api/auth/signup` (email+password)
- `POST /api/auth/logout`

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Left panel | Login form containing: Log in with Google button, email input, password input, Log in button, Create your account link, and Forgot password? link | Left side of split page |
| Right panel | Promotional graphic with tagline summarizing Atoms benefits | Right side of split page |
| Header | Atoms logo linking to home | Top of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Log in with Google | Initiates OAuth login via Google |
| Input | Email and password fields | User enters credentials |
| Click | Log in | Submits credentials to authenticate (requires valid account) |
| Click | Create your account | Navigates to sign-up page (Page_14_SignUp) |
| Click | Forgot password? | Opens password reset process |
| Click | Atoms logo | Returns to home page |

Entry/Exit:
- Entry: From Log in button on home or other pages.
- Exit: Submission of credentials or navigating to sign-up or password reset pages; returning home via logo.

## Page_14_SignUp (Page 14 - Sign Up)

Purpose: Enables new users to create an Atoms account by entering personal details and agreeing to terms. Due to rate-limit restrictions on the image generator, a dedicated screenshot could not be produced; the login page screenshot (page_13_login.png) is used here as a placeholder.

Screenshot: `screenshots/page_14_signup.png`
Note: page_14_signup.png (placeholder)

Frontend mapping:
- Route: `/signup`
- Next.js file (planned): `apps/web/app/(auth)/signup/page.tsx`

Backend mapping:
- `GET /api/auth/oauth/google/start` (DOC: required)
- `GET /api/auth/oauth/github/start` (MANDATORY requirement)
- `GET /api/auth/oauth/{provider}/callback`
- `POST /api/auth/login` (email+password)
- `POST /api/auth/signup` (email+password)
- `POST /api/auth/logout`

Visible UI Components:
| Component type | Label/text | Location |
| --- | --- | --- |
| Registration form | Fields for username, email address, password, confirm password | Central column |
| Google sign-up button | Sign up with Google | Above or below form inputs |
| Create account button | Primary button to submit registration | Below input fields |
| Agreement notice | Text noting acceptance of Terms of Service and Privacy Policy with links | Under sign-up button |
| Log in link | Log in now link for existing users | Bottom of form |
| Header | Atoms logo linking to home | Top of page |

Interactions:
| Action type | Element/label | Expected outcome |
| --- | --- | --- |
| Click | Sign up with Google | Initiates OAuth sign-up |
| Input | Username, email, password fields | Enter user details |
| Click | Create account | Submits registration form; if successful user is logged in |
| Click | Log in now | Navigates back to login page |
| Click | Terms/Privacy links | Opens respective policy documents |
| Click | Atoms logo | Returns to home page |

Entry/Exit:
- Entry: From Sign up button on header or Create your account link in login page.
- Exit: After successful registration (not tested), user would be taken to dashboard; otherwise they can navigate back to login or home via links.

## Appendix: Referenced But Not Specified (UNKNOWN)

- Password reset process (triggered by `Forgot password?` on Login)
- Terms of Service page/content (linked from Sign Up)
- Privacy Policy page/content (linked from Sign Up)
- Any authenticated “dashboard/app” pages (not present in UI docs; will be added minimally to satisfy mandatory LangGraph requirements)
