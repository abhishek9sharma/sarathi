prompt_formats = {
    "autocommit": """ 
                         Your task is to generate a commit message based on the diff provided. Please follow below guidelines while generation the commits
                          - Think like a software developer
                          - Provide a high level description of changes
                          - Wrap lines at 72 characters
                          - In case of multiple lines Add - in front of each line
                          - Provide High Level Description
                          - User impertaive moodd in the subject line
                          - Use a maximum of 50 words
                          - Use standard English
                          - Try to be concise. Do not write multiple lines if not required
                        """
}
