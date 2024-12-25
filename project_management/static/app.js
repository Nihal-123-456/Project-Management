function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

const complete_task = (event, task_id) => {
    event.preventDefault();
    fetch(`/complete_task`,{
      method: 'PUT',
      headers:{
        'Content-type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({
        task_id: task_id
      })
    })
    .then((req)=>req.json())
    .then((data)=>{
      if(data['message']=='incomplete dependencies.'){
        alert('Cannot complete task. Dependency not fulfilled..')
      }
      else{
        window.location.reload()
      }
    })
}

const delete_task = (event, task_id) => {
  event.preventDefault();
  fetch(`/delete_task`,{
    method: 'DELETE',
    headers:{
      'Content-type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
      task_id: task_id
    })
  })
  .then((req)=>req.json())
  .then((data)=>{
    window.location.reload()
  })
}

const delete_project = (event, project_id) => {
  event.preventDefault()
  const path = window.location.pathname
  fetch('/delete_project', {
    method: 'DELETE',
    headers: {
      'Content-type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
      project_id: project_id
    })
  })
  .then((req)=>req.json())
  .then((data)=>{
    if(path.includes('dashboard')){
      window.location.reload()
    }
    else{
      window.location.href = '/dashboard#project-lists'
    }
  })
}

const complete_project = (event, project_id) => {
  event.preventDefault()
  fetch(`/complete_project`,{
    method: 'PUT',
    headers: {
      'Content-type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
      project_id: project_id
    })
  })
  .then((res)=>res.json())
  .then((data)=>{ 
    if(data['message']=='incomplete tasks.'){
      alert('This project has tasks which are yet to be completed.')
    }
    else{
      window.location.reload()
    }
  })
}

function formatTimeSpent(timeSpent) {
  let [hours, minutes, seconds] = timeSpent.split(':');
  seconds = seconds.split('.')[0];
  hours = String(hours).padStart(2, '0');
  minutes = String(minutes).padStart(2, '0');
  seconds = String(seconds).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

const start_stop_clock = (event, task_id) => {
  event.preventDefault()
  fetch('/start_stop_clock', {
    method: 'POST',
    headers: {
      'Content-type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({
      task_id: task_id
    })
  })
  .then((res)=>res.json())
  .then((data)=>{
    if(data['message'] == 'Timer has started.'){
      document.querySelectorAll(`#clock-symbol-${task_id}`).forEach((element)=>{
        element.innerText = 'pause'
      })
      document.querySelectorAll(`#clock-name-${task_id}`).forEach((element)=>{
        element.innerText = 'Stop Timer'
      })
      document.querySelectorAll(`#clock-div-${task_id}`).forEach((element)=>{
        element.style.backgroundColor = 'green'
      })
    }
    else if(data['message'] == 'Timer has stopped.'){
      document.querySelectorAll(`#clock-symbol-${task_id}`).forEach((element)=>{
        element.innerText = 'not_started'
      })
      document.querySelectorAll(`#clock-name-${task_id}`).forEach((element)=>{
        element.innerText = 'Start Timer'
      })
      document.querySelectorAll(`#clock-div-${task_id}`).forEach((element)=>{
        element.style.backgroundColor = 'rgb(132, 198, 33)'
      })
      const formatted_time = formatTimeSpent(data['time_spent'])
      document.querySelectorAll(`#time-spent-${task_id}`).forEach((element)=>{
        element.innerText = formatted_time
      })
    }
    else{
      alert(data['message'])
    }
  })
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('ongoing-task-btn').addEventListener('click', () => {load_task_list('ongoing_tasks')})
  document.getElementById('completed-task-btn').addEventListener('click', () => {load_task_list('completed_tasks')})
  document.getElementById('overdue-task-btn').addEventListener('click', () => {load_task_list('overdue_tasks')})
  document.getElementById('all-task-btn').addEventListener('click', () => {load_task_list('all_tasks')})
});

const load_task_list = (task_type) => {
  all = document.getElementById('all_tasks')
  ongoing = document.getElementById('ongoing_tasks')
  completed = document.getElementById('completed_tasks')
  overdue = document.getElementById('overdue_tasks')
  ongoing_btn = document.getElementById('ongoing-task-btn')
  completed_btn = document.getElementById('completed-task-btn')
  overdue_btn = document.getElementById('overdue-task-btn')
  all_btn = document.getElementById('all-task-btn')
  if (task_type=='ongoing_tasks'){
    all_btn.style.color = 'black'
    all_btn.style.backgroundColor = 'white'

    ongoing_btn.style.color = 'white'
    ongoing_btn.style.backgroundColor = '#4C3575'

    overdue_btn.style.color = 'black'
    overdue_btn.style.backgroundColor = 'white'

    completed_btn.style.color = 'black'
    completed_btn.style.backgroundColor = 'white'

    all.style.display = 'none'
    ongoing.style.display = 'block'
    completed.style.display = 'none'
    overdue.style.display = 'none'
  }
  else if (task_type=='overdue_tasks'){
    all_btn.style.color = 'black'
    all_btn.style.backgroundColor = 'white'

    overdue_btn.style.color = 'white'
    overdue_btn.style.backgroundColor = '#4C3575'

    ongoing_btn.style.color = 'black'
    ongoing_btn.style.backgroundColor = 'white'

    completed_btn.style.color = 'black'
    completed_btn.style.backgroundColor = 'white'

    all.style.display = 'none'
    ongoing.style.display = 'none'
    completed.style.display = 'none'
    overdue.style.display = 'block'
  }
  else if (task_type=='all_tasks'){
    all_btn.style.color = 'white'
    all_btn.style.backgroundColor = '#4C3575'

    overdue_btn.style.color = 'black'
    overdue_btn.style.backgroundColor = 'white'

    ongoing_btn.style.color = 'black'
    ongoing_btn.style.backgroundColor = 'white'

    completed_btn.style.color = 'black'
    completed_btn.style.backgroundColor = 'white'

    all.style.display = 'block'
    ongoing.style.display = 'none'
    completed.style.display = 'none'
    overdue.style.display = 'none'
  }
  else{
    all_btn.style.color = 'black'
    all_btn.style.backgroundColor = 'white'
    
    completed_btn.style.color = 'white'
    completed_btn.style.backgroundColor = '#4C3575'

    overdue_btn.style.color = 'black'
    overdue_btn.style.backgroundColor = 'white'

    ongoing_btn.style.color = 'black'
    ongoing_btn.style.backgroundColor = 'white'

    all.style.display = 'none'
    ongoing.style.display = 'none'
    completed.style.display = 'block'
    overdue.style.display = 'none'
  }
}

load_task_list('all_tasks')