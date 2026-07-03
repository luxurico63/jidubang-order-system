streamlit.errors.StreamlitDuplicateElementId: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:
File "/mount/src/jidubang-order-system/app.py", line 111, in <module>
    rest_name = st.text_input("식당 이름")
                ~~~~~~~~~~~~~^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 698, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/text_widgets.py", line 320, in text_input
    return self._text_input(
           ~~~~~~~~~~~~~~~~^
        label=label,
        ^^^^^^^^^^^^
    ...<15 lines>...
        ctx=ctx,
        ^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/widgets/text_widgets.py", line 374, in _text_input
    element_id = compute_and_register_element_id(
        "text_input",
    ...<13 lines>...
        width=width,
    )
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 261, in compute_and_register_element_id
    _register_element_id(ctx, element_type, element_id)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/elements/lib/utils.py", line 146, in _register_element_id
    raise StreamlitDuplicateElementId(element_type)
