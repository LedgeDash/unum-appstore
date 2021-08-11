# Text Processing

![text-processing-app](https://github.com/LedgeDash/unum-appstore/blob/main/text-processing/text-processing-app.jpg)

An example workflow for processing and creating social network posts.

## Input

The workflow takes a text message as input. The message can include user mentions (e.g., `@ABCNews`) and URLs.

The `UserMention` function extracts the usernames in the message. The `FindUrl` function returns all URLs in the message as a list. `ShortenUrl` creates a shortened URL for each URL found by `FindUrl` and return a list of tuples with each tuple being `(original_url, shortened_url)`.

Once both `UserMention` and `ShortenUrl` completes, `CreatePost` is invoked with `UserMention`'s return value and `ShortenUrl`'s return value. Inputs to `CreatePost` are formatted as lists with `UserMention`'s return value at the 0th index and `ShortenUrl`'s return value at the 1st index.

`CreatePost` creates a JSON document of the following format:

```json
{
        "user_names": ["bob", "alice"],
        "urls": [["https://some.looooooooooooong-url.com","https://sh.ort/yi"],["https://someother.looooooooooooong-url.com","https://sh.ort/er"]]
}

```

The `Publish` function saves the JSON document in a database created by the programmer.