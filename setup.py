from setuptools import setup

setup(
        name='mailcontrols',
        version='0.3',
        packages=['mailcontrols', 'mailcontrols.filter_plugins', 'mailcontrols.admin'],
        url='https://github.com/tmajibon/mailcontrols',
        license='',
        author='Christopher Martin',
        author_email='chris@foggyminds.com',
        description='Remote programmatic control over email inboxes via IMAP/IDLE.',
        install_requires=[
            'IMAPClient>=0.13',
            'requests>=2.2.1',
            'SQLAlchemy>=0.8.4',
            'bottle',
            'jinja2'
        ],
        scripts=[
            'mailcontrols/bin/mailcontrols'
        ],
        include_package_data=True,
        zip_safe=True
)
