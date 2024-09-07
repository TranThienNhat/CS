document.addEventListener('DOMContentLoaded', function() {
  
  // Use buttons to toggle between views
  document.querySelector('#compose-form').addEventListener('submit', sentEmail);
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);
  

  // By default, load the inbox
  load_mailbox('inbox');
});

function compose_email() {
  
  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';
  
  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';
}

function load_mailbox(mailbox) {
  // Hiển thị danh sách email và ẩn các chế độ xem khác
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#email-detail-view').style.display = 'none';

  // Hiển thị tên hộp thư
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Gửi yêu cầu lấy danh sách email từ máy chủ
  fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
      // Thêm mỗi email vào danh sách
      emails.forEach(email => {
        const emailElement = document.createElement('div');
        emailElement.className = `list-group-item ${email.read ? 'bg-light' : 'bg-secondary'}`;
        emailElement.innerHTML = `
          <strong>From:</strong> ${email.sender} <br>
          <strong>Subject:</strong> ${email.subject} <br>
          <strong>Timestamp:</strong> ${email.timestamp}
        `;

        // Gán sự kiện click cho email
        emailElement.addEventListener('click', () => {
          email_views(email.id);
        });

        // Thêm email vào danh sách
        document.querySelector('#emails-view').appendChild(emailElement);
      });
    })
    .catch(error => console.error('Error loading mailbox:', error));
}



function sentEmail(event) {
  event.preventDefault();

  const recipients = document.querySelector('#compose-recipients').value.trim();
  const subject = document.querySelector("#compose-subject").value.trim();
  const body = document.querySelector('#compose-body').value.trim();

  if (!recipients) {
    alert('Please enter at least one recipient.');
    return;
  }

  fetch('/emails', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        recipients: recipients,
        subject: subject,
        body: body
    })
  })
  .then(response => response.json())
  .then(result => {
    if (result.error) {
      console.error(result.error);
      alert(`Error: ${result.error}`);
    } else {
      console.log(result.message);
      load_mailbox('sent');
      ;
    }
  })
  .catch(error => {
    console.error('Network error:', error);
    alert('A network error occurred.');
  });
}

function email_views(id) {
  fetch(`/emails/${id}`)
  .then(response => response.json())
  .then(email => {
    // Hide all views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';
    document.querySelector('#email-detail-view').style.display = 'block';

    document.querySelector('#email-detail-view').innerHTML = `
      <div class="list-group">
        <div class="list-group-item"><strong>From:</strong> ${email.sender}</div>
        <div class="list-group-item"><strong>To:</strong> ${email.recipients}</div>
        <div class="list-group-item"><strong>Subject:</strong> ${email.subject}</div>
        <div class="list-group-item"><strong>Timestamp:</strong> ${email.timestamp}</div>
        <div class="list-group-item"><p>${email.body}</p></div>
      </div>
    `;

    if (!email.read) {
      fetch(`/emails/${email.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            read: true
        })
      });
    }

    // Create and append archive button
    const archive_btn = document.createElement('button');
    archive_btn.innerHTML = email.archived ? 'Unarchive' : 'Archive';
    archive_btn.className = email.archived ? 'btn btn-danger' : 'btn btn-success';
    archive_btn.addEventListener('click', function() {
        fetch(`/emails/${email.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              archived: !email.archived
          })
        })
        .then(() => load_mailbox('archive'));
    });
    document.querySelector('#email-detail-view').append(archive_btn);

    // Create and append reply button
    const reply_btn = document.createElement('button');
    reply_btn.innerHTML = 'Reply';
    reply_btn.className = 'btn btn-info';
    reply_btn.addEventListener('click', function() {
        compose_email();

        document.querySelector('#compose-recipients').value = email.sender;
        let subject = email.subject;
        if (!subject.startsWith('Re:')) {
          subject = `Re: ${email.subject}`;
        }
        document.querySelector('#compose-subject').value = subject;
        document.querySelector('#compose-body').value = `${email.body}\n`;
    });
    document.querySelector('#email-detail-view').append(reply_btn);
  });
}
