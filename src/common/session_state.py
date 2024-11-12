import streamlit as st
import uuid

class SessionState:
    def __init__(self, **kwargs):
        """A new SessionState object.
        Parameters
        ----------
        **kwargs : any
            Default values for the session state.
        Example
        -------
        >>> session_state = SessionState(user_name='', favorite_color='black')
        >>> session_state.user_name = 'Mary'
        >>> session_state.favorite_color
        'black'
        """
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __call__(self, **kwargs):
        """Gets a SessionState object for the current session.
        Creates a new object if necessary.
        Parameters
        ----------
        **kwargs : any
            Default values you want to add to the session state, if we're creating a new one.
        Example
        -------
        >>> session_state = get_session_state(user_name='', favorite_color='black')
        >>> session_state.user_name
        >>> session_state.user_name = 'Mary'
        >>> session_state.favorite_color
        'black'
        """
        for key, val in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, val)
        return self

def get_session_state(**kwargs):
    """Gets a SessionState object for the current session.
    Creates a new object if necessary.
    Parameters
    ----------
    **kwargs : any
        Default values you want to add to the session state, if we're creating a new one.
    Example
    -------
    >>> session_state = get_session_state(user_name='', favorite_color='black')
    >>> session_state.user_name
    >>> session_state.user_name = 'Mary'
    >>> session_state.favorite_color
    'black'
    """
    session_id = st.session_state.get('_session_state_id')
    if session_id is None:
        session_id = str(uuid.uuid4())
        st.session_state['_session_state_id'] = session_id

    if session_id not in st.session_state:
        st.session_state[session_id] = SessionState(**kwargs)

    return st.session_state[session_id]

# # Example usage:
# session_state = get_session_state(user_name='', favorite_color='black')
# st.write(session_state.user_name)
# session_state.user_name = st.text_input('User name', session_state.user_name)
# st.write(session_state.favorite_color)
# session_state.favorite_color = st.text_input('Favorite color', session_state.favorite_color)
