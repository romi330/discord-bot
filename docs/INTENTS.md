# Required Privileged Intents

## 📄 `message_content` Intent

### Why It's Necessary

The bot requires access to the `message_content` intent to enable essential features for moderation, user interaction, and dynamic command handling. These features are critical for maintaining a safe and engaging environment in your server.

### Features Enabled by `message_content`

- **Moderation Tools**:
  - Detect and block inappropriate content (e.g., profanity, slurs, or malicious links).
  - Prevent spam and repeated messages.
  - Identify and mitigate message flooding or excessive emoji usage.
- **User Interaction**:
  - Respond to mentions (e.g., `@paul`) with automated replies.
  - Enhance accessibility for new members by providing helpful responses.
- **Spam and Flood Detection**:
  - Detect repeated or fast messages to prevent raids or spam attacks.
  - Alert moderators automatically when suspicious activity is detected.

### Privacy Commitment

The bot only processes message content when necessary for the features described above. No message content is stored or logged beyond what is required for functionality. We are committed to ensuring user privacy and data security.

---

## 👥 `guild_members` Intent

### Why It's Necessary

The bot requires access to the `guild_members` intent to enable features that rely on member data. These features are essential for server management and moderation.

### Features Enabled by `guild_members`

- **Auto-Role System**:
  - Automatically assign roles to new members upon joining.
- **Member Tracking**:
  - Detect when members join or leave the server.
- **Moderation Tools**:
  - Enable commands like `/timeout`, `/ban`, and `/kick` that depend on member information.
- **User Information**:
  - Fetch member details for commands like `/userinfo` or `/modmail`.

### Privacy Commitment

The bot only processes member data when necessary for the features described above. No member data is stored or logged beyond what is required for functionality. We are committed to ensuring user privacy and data security.
