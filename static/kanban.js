/* eslint-env es6 */
/* global Vue, axios */

/* eslint indent: ["error", 2] */
/* exported app, dragstart_handler, dragover_handler,
 dragleave_handler, drop_handler */
/* eslint quote-props: ["error", "as-needed"] */
/* eslint func-names: ["error", "never"] */
/* eslint id-length: ["error", { "exceptions": ["i"] }] */
/* eslint no-magic-numbers: ["error", { "ignore": [0, 1] }] */

window.app = new Vue({
  data: {
    tagids: [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
    tagid_colors: ["red", "green", "yellow", "aqua", "brown", "#DC143C", "#7FFF00", "#A9A9A9", "#8B008B", "#ADFF2F"],
    cards: [],
    columns: [],
    edit_card: null,
    show_archived_cards: false,
    show_card_ids: false,
    show_card_timestamps: false,
    show_only_near_due: false,
    file: null,
    file_url: null
  },
  el: "#kanban",
  methods: {
    show_card_or_not: function(card, column) {
        // filter cards on other columns
        if (card.column !== column) {
            return false;
        }
        // filter archived cards or not
        if (card.archived === true && !this.show_archived_cards) {
            return false;
        }
        // filter cards per due date
        if (this.show_only_near_due === true) {
            // filter ones without due date.
            if (!check_due_date(card.due_date)) {
                return false;
            }
            // filter ones with due date in far future
            let due = new Date(card.due_date);
            if (date_due(due, 3)) {
                return false;
            }
        }
        return true;
    },
    reset_card_edit: function() {
      this.edit_card = null;
      this.file = null;
      this.file_url = null;
    },
    on_file_change: function(e) {
        this.file = e.target.files[0];
        this.compress(this.file);     
    },
    compress: function(original_file) {
        const fileName = original_file.name;
        const reader = new FileReader();
        reader.readAsDataURL(original_file);
        reader.onload = event => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                const elem = document.createElement('canvas');
                // scale down image process
                const max_width = 250;
                const max_height = 150;
                // first the real scale factor
                let width_scale = max_width / img.width;
                let height_scale = max_height / img.height;

                let scale_factor = null;
                if (width_scale < height_scale) {
                    scale_factor = width_scale;
                } else {
                    scale_factor = height_scale;
                }
                // scale factor computed
                console.log("computed scale factor for image: " + scale_factor);
                
                // scale down image
                elem.width = img.width * scale_factor;
                elem.height = img.height * scale_factor;

                const ctx = elem.getContext('2d');
                // img.width and img.height will give the original dimensions
                ctx.drawImage(img, 0, 0, elem.width,  elem.height);
                this.file_url = elem.toDataURL();
            },
            reader.onerror = error => console.log(error);
        };
    },
    file_remove: function(e) {
        console.log("file_remove");
        this.file = null;
        this.file_url = null;
    },
    file_display_name: function(e) {
        if (this.edit_card !== null) {
            // case overwrite a file by adding using on_file_change
            if (this.file !== null) {
                return this.file.name;
            }
            // case we use the old file
            if (this.edit_card.image_name !== null) {
                return this.edit_card.image_name;
            }
            // case we show notting
            return null;
            
        }
    },
    cancel_card_edit: function () {
      console.log("cancel_card_edit");
      reset_card_edit();
    },
    complete_card_edit: function (card_id) {
      console.log("complete_card_edit");
      if (this.edit_card) {
        this.update_card(card_id);
        
        /* refresh the current data */
        this.edit_card.text = this.$refs.card_edit_text.value;
        this.edit_card.archived = this.$refs.card_edit_archive.checked;
        this.edit_card.due_date = this.$refs.card_edit_due.value;
        
		tags = []
		for (i=0; i<this.$refs.card_edit_tag.length; i++) {
		  comp = this.$refs.card_edit_tag[i];
		  if (comp.checked) {
		    extracted_id = comp.id.substring("card_edit_tag".length);
		    tags.push({"id": parseInt(extracted_id)});
		  }

		}
		this.edit_card.tags = tags;
        
        this.edit_card = null;
      }
    },
    create_card: function (ev) {
      let vue_app = this;
      let form = ev.target;

      axios.post(form.action, new FormData(form)).then(function () {
        vue_app.refresh_cards();
        form.reset();
      });
    },
    delete_card: function (card_id) {
      let vue_app = this;

      if (window.confirm("Delete card?")) {
        axios.delete("card/" + card_id).then(function () {
          for (let i = 0; i < vue_app.cards.length; i += 1) {
            if (vue_app.cards[i].id === card_id) {
              vue_app.reset_card_edit();
              delete vue_app.cards[i];
              vue_app.cards.splice(i, 1);

              return;
            }
          }
        });
      }
    },
    get_card: function (id) {
      let target = id;

      if (typeof target === "string") {
        target = parseInt(target.replace("card", ""), 10);
      }
      for (let i = 0; i < this.cards.length; i += 1) {
        if (this.cards[i].id === target) {
          return this.cards[i];
        }
      }
    },
    handle_card_edit_click: function (ev) {
      console.log("handle_card_edit_click");
      if (ev.target === this.$refs.card_edit_container) {
        //this.edit_card = null;
        this.reset_card_edit();
      }
    },
    refresh_cards: function () {
      let vue_app = this;

      axios.get("cards").then(function (response) {
        vue_app.cards = response.data;
      });
    },
    refresh_columns: function () {
      let vue_app = this;

      axios.get("columns").then(function (response) {
        vue_app.columns = response.data;
        document.documentElement.style.setProperty(
          "--kanban-columns",
          vue_app.columns.length
        );
      });
    },
    start_card_edit: function (card_id) {
      this.edit_card = this.get_card(card_id);
      if (this.edit_card.image_fs_name !== null) {
        this.file_url = 'images/' + this.edit_card.image_fs_name
      }

      let vue_app = this;

      Vue.nextTick(function () {
        vue_app.$refs.card_edit_text.value = vue_app.edit_card.text;
        vue_app.$refs.card_edit_text.focus();
        vue_app.$refs.card_edit_text.select();
      });
    },
    update_card: function (id) {
      /* craft uuid name for the file*/
      let file_updated = (window.app.file !== null);
      if (file_updated) {
          let filename = window.app.file.name;
          let file_ext = filename.substring(filename.lastIndexOf('.')+1, filename.length) || filename;
          let uuid = guid();
          let new_file_name = uuid + '.' + file_ext;
        
          /* https://serversideup.net/uploading-files-vuejs-axios/ */
          let file = window.app.file_url;
          let formData = new FormData();
          formData.append('file_data', file);
          formData.append('file_name', filename);
          formData.append('new_file_name', new_file_name);
          
          axios.post('/upload-file/' + id, formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            }
          ).then(function(response){
            let c = window.app.get_card(id);       
            c.image_fs_name = new_file_name;
          }).catch(function(exc){
            console.log('FAILURE!!');
            console.log(exc);
          });
          
          
          window.app.file = null;
          window.app.file_url = null;
            
          /* update current field*/
          this.edit_card.image_name = filename;
          // do not update image_fs_name because it's updated asynchronously when upload succeeded.
      }
      let card = this.get_card(id);
      axios.put("card/" + card.id, card);
    },
    init: function () {
      this.refresh_columns();
      this.refresh_cards();
    }
  }
});

function dragstart_handler (ev) {
  // Add the target element's id to the data transfer object
  ev.dataTransfer.setData("text/plain", ev.target.id);
  ev.dropEffect = "move";
}

function dragover_handler (ev) {
  ev.preventDefault();
  // Set the dropEffect to move
  ev.dataTransfer.dropEffect = "move";

  let container = ev.target;

  while (container.tagName !== "SECTION") {
    container = container.parentElement;
  }

  if (!container.classList.contains("drop-target")) {
    container.classList.add("drop-target");
  }
}

function dragleave_handler (ev) {
  let container = ev.target;

  while (container.tagName !== "SECTION") {
    container = container.parentElement;
  }
  container.classList.remove("drop-target");
}

function drop_handler (ev) {
  ev.preventDefault();

  // TODO: handle invalid card ID
  let card = window.app.get_card(ev.dataTransfer.getData("text"));
  let container = ev.target;

  while (container.tagName !== "SECTION") {
    container = container.parentElement;
  }
  container.classList.remove("drop-target");

  let new_col = container.getElementsByTagName("h2")[0].textContent;
  let column_cards = container.getElementsByTagName("li");
  let moving_down = false;
  let before_id = null;

  for (let i = 0; i < column_cards.length; i += 1) {
    if (parseInt(column_cards[i].id.replace("card", ""), 10) === card.id) {
      moving_down = true;
    }

    let event_absolute_y = ev.y + document.documentElement.scrollTop;

    // Mouse above list
    if (column_cards[i].offsetTop > event_absolute_y) {
      before_id = "all";
      break;
    // On list item
    } else if (i < (column_cards.length - 1) && event_absolute_y <= column_cards[i + 1].offsetTop) {
      if (moving_down) {
        before_id = parseInt(column_cards[i + 1].id.replace("card", ""), 10);
      } else {
        before_id = parseInt(column_cards[i].id.replace("card", ""), 10);
      }
      break;
    } else if (i === (column_cards.length - 1)) {
      // On last list item
      if (event_absolute_y < column_cards[i].offsetTop + (column_cards[i].offsetHeight) && card.column !== new_col) {
        before_id = parseInt(column_cards[i].id.replace("card", ""), 10);
      // Past the end
      } else {
        before_id = null;
      }
    }
  }
  if (column_cards.length > 0 && card.id !== before_id) {
    axios.post("card/reorder", {
      before: before_id,
      card: card.id
    }).then(function () {
      window.app.refresh_cards();
    });
  }
  if (card.column !== new_col) {
    card.column = new_col;
    window.app.update_card(card.id);
  }
}


function tag_color(tagid) {
  for (i=0; i<window.app.tagids.length; i++) {
    if (tagid === window.app.tagids[i]) {
	  return window.app.tagid_colors[i]
	}
  }
  return "black"
}

function tag_checked(tagid, edit_card) {
  for (i=0; i<edit_card.tags.length; i++) {
    tag = edit_card.tags[i];
	if (tag.id === tagid) {
	  return true;
	 }
  }
  return false
}

function date_due(date, day_diff) {
    let now = new Date();
    /*now.setHours(0,0,0,0);*/
    
    let due = new Date(date.getTime());
    due.setDate(due.getDate() - day_diff);
    
    return (due > now)
}

function due_date_color(due_date) {
    /* due date is just a string */
    let due = new Date(due_date);
    
    if (date_due(due, 3)) {
        return "white";
    } else if (date_due(due, 2)) {
        return "green";
    } else if (date_due(due, 1)) {
        return "yellow";
    } else if (date_due(due, 0)) {
        return "orange";
    } else {
        return "red";
    }
}

function check_due_date(due_date) {
    if (due_date === null) {
        return false;
    }
    return due_date.includes("-");
}

function guid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  }
  return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
}

document.addEventListener("DOMContentLoaded", function () {
  window.app.init();
});
