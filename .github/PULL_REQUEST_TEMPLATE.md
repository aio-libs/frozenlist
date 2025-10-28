<!-- Thank you for your contribution! -->

## What do these changes do?

<!-- Please give a short brief about these changes. -->

## Are there changes in behavior for the user?

<!-- Outline any notable behaviour for the end users. -->

## Related issue number

<!-- Are there any issues opened that will be resolved by merging this change? -->

## Checklist

- [ ] I think the code is well written
- [ ] Unit tests for the changes exist
- [ ] Documentation reflects the changes
- [ ] If you provide code modifications, please add yourself to `CONTRIBUTORS.txt`
  * The format is &lt;Name&gt; &lt;Surname&gt;.
  * Please keep the list in alphabetical order, the file is sorted by name.
- [ ] Add a new news fragment into the `CHANGES` folder
  * name it `<issue_id>.<category>` for example (588.bugfix)
  * if you don't have an `issue_id` change it to the pr id after creating the pr
  * ensure category is one of the following:
    * `.bugfix`: Signifying a bug fix.
    * `.feature`: Signifying a new feature.
    * `.breaking`: Signifying a breaking change or removal of something public.
    * `.doc`: Signifying a documentation improvement.
    * `.packaging`: Signifying a packaging or tooling change that may be relevant to downstreams.
    * `.contrib`: Signifying an improvement to the contributor/development experience.
    * `.misc`: Anything that does not fit the above; usually, something not of interest to users.
  * Make sure to use full sentences with correct case and punctuation, for example: "Fix issue with non-ascii contents in doctest text files."
