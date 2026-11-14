# Addendum 2 (owner direct instruction; takes precedence). Continue.
- **Lift the Naver key hold:** use Naver as a demand signal. Read the client id and secret from the keychain (`security find-generic-password -s myeotnyeon.naver.client_id -w`, the same for `myeotnyeon.naver.client_secret`).
  - DataLab search trend (POST https://openapi.naver.com/v1/datalab/search): relative search volume for case keywords around the incident and the trial.
  - Search API (news/blog/cafe result counts).
  - **Never output the key values in logs, files, reports or commits.** Stay within the free call quota.
